# backend/routes/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from backend.utils.logger import get_logger
import shutil, os

router = APIRouter()
logger = get_logger(__name__)

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", summary="Upload a file for agent processing")
async def upload_file(file: UploadFile = File(...)):
    try:
        dest_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File uploaded: {file.filename}")
        return JSONResponse(content={"success": True, "file_id": file.filename})
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
