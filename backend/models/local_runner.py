# backend/models/local_runner.py
"""
Local model runner using HuggingFace Transformers + PEFT.
Supports:
  - Plain causal LM models (e.g., DAN-Qwen3-1.7B)
  - LoRA-adapted models via PEFT (e.g., Qwen3-14B + WMDP cyber adapter)
Models are loaded on-demand and cached in RAM for reuse.
"""
import logging
import threading
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Model registry ────────────────────────────────────────────────────────────
# Plain models: id → {"hf_path": str}
# LoRA  models: id → {"base": str, "adapter": str}
LOCAL_MODEL_REGISTRY = {
    "local:dan-qwen": {
        "type":    "causal",
        "hf_path": "UnfilteredAI/DAN-Qwen3-1.7B",
    },
    "local:qwen3-cyber": {
        "type":    "lora",
        "base":    "willcb/Qwen3-14B",
        "adapter": "exploration-hacking/qwen3-14b-wmdp-conditional-lora",
    },
}

# Cache: model_id → (model, tokenizer) — loaded once, held in RAM
_model_cache: dict = {}
_cache_lock  = threading.Lock()


# ─── Device detection ──────────────────────────────────────────────────────────
def _best_device() -> str:
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


# ─── Loaders ───────────────────────────────────────────────────────────────────
def _load_causal(cfg: dict):
    """Load a plain causal LM (no LoRA)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    path   = cfg["hf_path"]
    device = _best_device()
    logger.info(f"Loading causal model '{path}' on {device}…")

    tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        path,
        trust_remote_code=True,
        torch_dtype=torch.float16 if device in ("mps", "cuda") else torch.float32,
    ).to(device)

    logger.info(f"  ✓ Causal model ready: {path}")
    return model, tokenizer


def _load_lora(cfg: dict):
    """Load a base model and attach a LoRA adapter via peft."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    base_path    = cfg["base"]
    adapter_path = cfg["adapter"]
    device       = _best_device()

    logger.info(f"Loading LoRA base '{base_path}' on {device}…")
    tokenizer = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)

    base_model = AutoModelForCausalLM.from_pretrained(
        base_path,
        trust_remote_code=True,
        torch_dtype=torch.float16 if device in ("mps", "cuda") else torch.float32,
    ).to(device)

    logger.info(f"  ✓ Base ready — attaching LoRA adapter '{adapter_path}'…")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()

    logger.info(f"  ✓ LoRA model ready: {adapter_path}")
    return model, tokenizer


def _load_model(model_id: str):
    cfg  = LOCAL_MODEL_REGISTRY[model_id]
    kind = cfg.get("type", "causal")
    if kind == "lora":
        return _load_lora(cfg)
    return _load_causal(cfg)


def get_model(model_id: str):
    """Return (model, tokenizer) from cache, loading on first access."""
    with _cache_lock:
        if model_id not in _model_cache:
            _model_cache[model_id] = _load_model(model_id)
        return _model_cache[model_id]


# ─── Inference ─────────────────────────────────────────────────────────────────
def generate_local(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> str:
    """
    Run inference with a locally loaded model.
    Returns the assistant reply text only (no special tokens, no system/user prefix).
    """
    import torch

    model, tokenizer = get_model(model_id)
    device = next(model.parameters()).device

    chat = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    # Try chat template first; fall back to simple prompt concatenation
    try:
        inputs = tokenizer.apply_chat_template(
            chat,
            add_generation_prompt=True,
            return_tensors="pt",
            enable_thinking=False,
        )
    except Exception:
        raw = f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:"
        inputs = tokenizer(raw, return_tensors="pt").input_ids

    inputs    = inputs.to(device)
    input_len = inputs.shape[-1]

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = outputs[0][input_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


# ─── Helpers ───────────────────────────────────────────────────────────────────
def is_available(model_id: str) -> bool:
    return model_id in LOCAL_MODEL_REGISTRY
