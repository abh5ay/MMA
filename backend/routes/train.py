# backend/routes/train.py
"""
Model Training Pipeline Route
POST /api/train  — download dataset, train model, save it, return metrics + serve endpoint
GET  /api/train/predict  — run inference on saved model
GET  /api/train/status   — check training status
"""
import os, json, threading, traceback, uuid, logging
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

WORKSPACE = os.path.expanduser("~/Desktop/ml_workspace")
os.makedirs(WORKSPACE, exist_ok=True)

# In-memory training job tracker
jobs: dict = {}


class TrainRequest(BaseModel):
    dataset_url:  str
    target_column: Optional[str] = None   # CSV column to predict
    model_type:   Optional[str] = "auto"  # auto | classification | regression | nlp
    model_name:   Optional[str] = "my_model"
    epochs:       Optional[int] = 10
    test_size:    Optional[float] = 0.2


class PredictRequest(BaseModel):
    model_name: str
    input_data: dict   # {feature_name: value, ...}


def _run_training(job_id: str, req: TrainRequest):
    """Background thread: download → detect → train → save → report."""
    job = jobs[job_id]
    model_dir = os.path.join(WORKSPACE, req.model_name)
    os.makedirs(model_dir, exist_ok=True)

    try:
        import subprocess, pandas as pd, numpy as np, zipfile, csv, io, shutil
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (accuracy_score, mean_squared_error,
                                     classification_report)
        import joblib

        # ── Step 1: Download dataset ──────────────────────────────────────────
        job["status"] = "downloading"
        raw_url = req.dataset_url.strip()

        # ── Normalise popular URL patterns ────────────────────────────────────
        # Kaggle dataset page  →  direct CSV via kaggle datasets download is not
        # available without auth, so we point users to a raw CSV mirror or
        # surface a clear error instead of silently downloading HTML.
        if "kaggle.com/datasets" in raw_url and not raw_url.endswith(".csv"):
            raise RuntimeError(
                "Kaggle dataset page URLs cannot be downloaded directly (login required). "
                "Please provide a direct raw CSV URL instead.\n"
                "💡 Tip: Open the dataset on Kaggle → click the CSV file → copy the raw/download URL, "
                "OR use a mirror like: https://raw.githubusercontent.com/... or any public direct CSV link."
            )

        # GitHub blob → raw
        if "github.com" in raw_url and "/blob/" in raw_url:
            raw_url = raw_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        job["log"].append(f"⬇️  Downloading dataset from {raw_url}")

        # Determine local file extension
        url_path = raw_url.split("?")[0]
        ext = url_path.split(".")[-1].lower()
        local_ext = ext if ext in ("csv", "json", "tsv", "zip") else "csv"
        data_path = os.path.join(model_dir, f"dataset.{local_ext}")

        result = subprocess.run(
            ["curl", "-L", "-A", "Mozilla/5.0",
             "-w", "%{http_code}",   # write HTTP status to stdout
             "-o", data_path, raw_url],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"Download failed: {result.stderr}")
        http_code = result.stdout.strip()
        if http_code and http_code != "200":
            raise RuntimeError(
                f"URL returned HTTP {http_code}. "
                "Please check the URL is a valid, publicly accessible direct download link."
            )

        # ── Unzip if needed ───────────────────────────────────────────────────
        if data_path.endswith(".zip"):
            job["log"].append("📦 Extracting zip archive…")
            with zipfile.ZipFile(data_path, "r") as zf:
                csv_files = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if not csv_files:
                    raise RuntimeError("No CSV file found inside the zip archive.")
                zf.extract(csv_files[0], model_dir)
                data_path = os.path.join(model_dir, csv_files[0])
            job["log"].append(f"✅ Extracted → {data_path}")
        else:
            # Sanity-check: make sure we didn't download an HTML error page
            with open(data_path, "r", errors="replace") as f:
                head = f.read(512)
            if head.strip().lower().startswith("<!doctype") or "<html" in head.lower():
                raise RuntimeError(
                    "The URL returned an HTML page, not a dataset file. "
                    "Please provide a direct download link to a CSV/JSON/TSV file."
                )

        job["log"].append(f"✅ Dataset saved → {data_path}")

        # ── Step 2: Load & inspect ────────────────────────────────────────────
        job["status"] = "loading"
        if data_path.endswith(".json"):
            df = pd.read_json(data_path)
        elif data_path.endswith(".tsv"):
            df = pd.read_csv(data_path, sep="\t")
        else:
            # Auto-detect delimiter (handles CSV, semicolon-CSV, tab, etc.)
            with open(data_path, "r", errors="replace") as f:
                sample = f.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                sep = dialect.delimiter
            except csv.Error:
                sep = ","
            df = pd.read_csv(data_path, sep=sep, engine="python")

        # ── Validate the loaded dataframe ─────────────────────────────────────
        if df.empty or len(df) == 0:
            raise RuntimeError(
                "The downloaded file loaded as an empty dataframe (0 rows). "
                "The URL may be returning a 404/error page or an empty file. "
                "Please verify the URL points to actual data."
            )
        if len(df.columns) < 2:
            raise RuntimeError(
                f"Dataset has only {len(df.columns)} column(s): {list(df.columns)}. "
                "A valid dataset needs at least 2 columns (features + target). "
                "Check that the URL points to a proper CSV file."
            )

        job["log"].append(f"📊 Loaded {len(df)} rows × {len(df.columns)} columns")
        job["shape"] = {"rows": len(df), "cols": len(df.columns), "columns": list(df.columns)}

        # Auto-detect target column
        target = req.target_column
        if not target:
            # Heuristic: last column, or column named label/target/class/y
            hints = [c for c in df.columns if c.lower() in
                     ("label","target","class","y","output","result","prediction")]
            target = hints[0] if hints else df.columns[-1]
        job["log"].append(f"🎯 Target column: {target}")

        # ── Step 3: Preprocess ────────────────────────────────────────────────
        job["status"] = "preprocessing"
        df = df.dropna()
        X = df.drop(columns=[target])
        y = df[target]

        # Encode categoricals
        from sklearn.preprocessing import LabelEncoder
        encoders = {}
        for col in X.select_dtypes(include=["object"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le

        # Detect task type
        task = req.model_type
        if task == "auto":
            n_unique = y.nunique()
            task = "classification" if (y.dtype == object or n_unique < 20) else "regression"
        job["log"].append(f"🤖 Task type: {task}")

        # Encode target if classification
        target_encoder = None
        if task == "classification" and y.dtype == object:
            target_encoder = LabelEncoder()
            y = target_encoder.fit_transform(y.astype(str))

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=req.test_size, random_state=42
        )

        # ── Step 4: Train ─────────────────────────────────────────────────────
        job["status"] = "training"
        if task == "classification":
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.svm import SVC

            models_to_try = {
                "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
                "Gradient Boosting":   GradientBoostingClassifier(n_estimators=100, random_state=42),
                "Logistic Regression": LogisticRegression(max_iter=1000),
            }
        else:
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.linear_model import LinearRegression, Ridge

            models_to_try = {
                "Random Forest":     RandomForestRegressor(n_estimators=100, random_state=42),
                "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
                "Linear Regression": LinearRegression(),
                "Ridge":             Ridge(),
            }

        best_model, best_score, best_name = None, -999, ""
        results = {}
        for name, model in models_to_try.items():
            job["log"].append(f"   Training {name}…")
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            if task == "classification":
                score = accuracy_score(y_test, preds)
                results[name] = {"accuracy": round(float(score), 4)}
            else:
                score = -mean_squared_error(y_test, preds, squared=False)  # negative RMSE
                results[name] = {"rmse": round(float(-score), 4)}
            if score > best_score:
                best_score, best_model, best_name = score, model, name

        job["log"].append(f"🏆 Best model: {best_name}")

        # ── Step 5: Save ──────────────────────────────────────────────────────
        model_path = os.path.join(model_dir, "model.pkl")
        meta_path  = os.path.join(model_dir, "meta.json")
        joblib.dump(best_model, model_path)

        feature_cols = list(X.columns)
        meta = {
            "model_name":    req.model_name,
            "task":          task,
            "target":        target,
            "features":      feature_cols,
            "best_model":    best_name,
            "all_results":   results,
            "dataset_url":   req.dataset_url,
            "encoders":      {k: list(v.classes_) for k, v in encoders.items()},
            "target_classes": list(target_encoder.classes_) if target_encoder else None,
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        job["log"].append(f"💾 Model saved → {model_path}")
        job["status"]   = "done"
        job["metrics"]  = results
        job["best"]     = best_name
        job["model_path"] = model_path
        job["meta"]     = meta
        job["log"].append("✅ Training complete!")

    except Exception as e:
        job["status"] = "error"
        job["error"]  = str(e)
        job["log"].append(f"❌ Error: {e}")
        logger.error(traceback.format_exc())


@router.post("/api/train")
def start_training(req: TrainRequest = Body(...)):
    """Start a training job and return job_id to poll status."""
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "queued", "log": [], "job_id": job_id}
    t = threading.Thread(target=_run_training, args=(job_id, req), daemon=True)
    t.start()
    return {"job_id": job_id, "message": "Training started"}


@router.get("/api/train/status/{job_id}")
def training_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return jobs[job_id]


@router.post("/api/train/predict/{model_name}")
def predict(model_name: str, req: PredictRequest = Body(...)):
    """Run inference on a saved model."""
    import joblib, pandas as pd
    model_dir  = os.path.join(WORKSPACE, model_name)
    model_path = os.path.join(model_dir, "model.pkl")
    meta_path  = os.path.join(model_dir, "meta.json")

    if not os.path.exists(model_path):
        return JSONResponse({"error": f"Model '{model_name}' not found"}, status_code=404)

    model = joblib.load(model_path)
    with open(meta_path) as f:
        meta = json.load(f)

    # Build feature row
    row = {feat: req.input_data.get(feat, 0) for feat in meta["features"]}
    df  = pd.DataFrame([row])
    pred = model.predict(df)[0]

    # Decode label if classification
    if meta.get("target_classes") and isinstance(pred, (int, float)):
        try: pred = meta["target_classes"][int(pred)]
        except: pass

    proba = None
    if hasattr(model, "predict_proba"):
        raw = model.predict_proba(df)[0]
        proba = {meta["target_classes"][i]: round(float(p), 4)
                 for i, p in enumerate(raw)} if meta.get("target_classes") else None

    return {"prediction": pred, "probabilities": proba, "model": model_name}


@router.get("/api/train/list")
def list_models():
    """List all trained models in workspace."""
    models = []
    for name in os.listdir(WORKSPACE):
        meta_path = os.path.join(WORKSPACE, name, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                models.append(json.load(f))
    return {"models": models}
