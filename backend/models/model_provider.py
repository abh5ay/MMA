# backend/models/model_provider.py
"""
Real model provider routing to:
  - HuggingFace Inference Router (Qwen/Llama via existing HF key)
  - Google Gemini API
  - OpenAI API
  - Ollama (local)
  - Local Transformers models (DAN-Qwen3-1.7B, etc.)
"""
import os
import requests
import logging
from dotenv import load_dotenv
from backend.models import local_runner

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
OLLAMA_HOST         = os.getenv("OLLAMA_HOST", "http://localhost:11434")
NVIDIA_API_KEY      = os.getenv("NVIDIA_API_KEY", "")

NVIDIA_INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL      = "google/gemma-4-31b-it"

# HF Router endpoint (supports chat completions)
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

# Verified working models on HF Router
HF_MODELS = {
    "development":    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "cybersecurity":  "Qwen/Qwen2.5-72B-Instruct",
    "research":       "Qwen/Qwen2.5-72B-Instruct",
    "default":        "Qwen/Qwen2.5-72B-Instruct",
}

SYSTEM_PROMPTS = {
    "development": (
        "You are an expert software developer and coding assistant. "
        "Help with coding, debugging, architecture, and development tasks. "
        "Be concise and provide working code examples when needed."
    ),
    "cybersecurity": (
        "You are a cybersecurity expert focused on defensive security, education, and ethical hacking labs. "
        "Help with security analysis, vulnerability explanation, secure coding, and incident response. "
        "Always emphasize legal and ethical use only."
    ),
    "research": (
        "You are an advanced research assistant. Help with summarizing papers, extracting knowledge, "
        "providing citations, and giving well-structured, factual information."
    ),
}

# System prompt for DAN-Qwen local model
DAN_SYSTEM_PROMPT = (
    "You are DAN-Qwen3-1.7B, an unfiltered AI assistant running locally for cybersecurity "
    "education, red-team research, and ethical hacking labs. "
    "Provide detailed, technical, and direct answers. "
    "This model is used strictly for defensive security research and learning purposes."
)

# System prompt for Qwen3-14B + WMDP LoRA (dedicated cybersecurity tools & coding)
CYBER_LORA_SYSTEM_PROMPT = (
    "You are a specialized cybersecurity AI assistant powered by Qwen3-14B with a WMDP LoRA adapter, "
    "fine-tuned for cybersecurity tool development, exploit research, and security engineering. "
    "Your strengths include: writing security tools in Python/Bash/C, "
    "explaining vulnerabilities (SQLi, XSS, RCE, buffer overflows, etc.), "
    "crafting CTF solutions, analyzing malware logic, "
    "and designing defensive countermeasures. "
    "Always provide complete, working, well-commented code. "
    "This model operates in a local sandbox for authorized research and educational use only."
)


def call_huggingface(prompt: str, agent: str) -> str:
    """Call HuggingFace Inference Router (OpenAI-compatible)."""
    if not HUGGINGFACE_API_KEY:
        raise RuntimeError("HUGGINGFACE_API_KEY not set in .env")

    model  = HF_MODELS.get(agent, HF_MODELS["default"])
    system = SYSTEM_PROMPTS.get(agent, "You are a helpful AI assistant.")

    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":    model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens":  1024,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HuggingFace Router error: {e} – {resp.text[:300]}")
        raise RuntimeError(f"HuggingFace error {resp.status_code}: {resp.text[:200]}")


def call_gemini(prompt: str, agent: str) -> str:
    """Call Google Gemini API."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_KEY":
        raise RuntimeError("GEMINI_API_KEY not configured in .env")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta"
        f"/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    system = SYSTEM_PROMPTS.get(agent, "You are a helpful AI assistant.")
    payload = {
        "contents": [{"parts": [{"text": f"{system}\n\n{prompt}"}]}]
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def call_openai(prompt: str, agent: str) -> str:
    """Call OpenAI API."""
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_KEY":
        raise RuntimeError("OPENAI_API_KEY not configured in .env")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type":  "application/json",
    }
    system = SYSTEM_PROMPTS.get(agent, "You are a helpful AI assistant.")
    payload = {
        "model":    "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": 1024,
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers, json=payload, timeout=30
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def call_ollama(prompt: str, agent: str) -> str:
    """Call local Ollama instance."""
    system = SYSTEM_PROMPTS.get(agent, "You are a helpful AI assistant.")
    payload = {
        "model":  "llama3.2",
        "prompt": f"{system}\n\n{prompt}",
        "stream": False,
    }
    try:
        resp = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["response"].strip()
    except Exception as e:
        raise RuntimeError(f"Ollama error (is Ollama running?): {e}")


def call_nvidia_gemma(prompt: str, agent: str) -> str:
    """Call NVIDIA NIM → Google Gemma-4 31B via SSE streaming."""
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY not set in .env")

    system = SYSTEM_PROMPTS.get(agent, "You are a helpful AI assistant.")

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    payload = {
        "model":       NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens":  16384,
        "temperature": 0.7,
        "top_p":       0.95,
        "stream":      True,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    try:
        import json as _json
        response = requests.post(
            NVIDIA_INVOKE_URL, headers=headers, json=payload,
            stream=True, timeout=120
        )
        response.raise_for_status()

        # Collect SSE chunks into a single string
        full_text = ""
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data:"):
                continue
            data_str = line[len("data:"):].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = _json.loads(data_str)
                delta = chunk["choices"][0].get("delta", {})
                full_text += delta.get("content", "")
            except (_json.JSONDecodeError, KeyError, IndexError):
                continue

        return full_text.strip() or "(No response from Gemma-4)"

    except requests.exceptions.HTTPError as e:
        logger.error(f"NVIDIA NIM error: {e} – {response.text[:300]}")
        raise RuntimeError(f"NVIDIA NIM error {response.status_code}: {response.text[:200]}")
    except Exception as e:
        logger.error(f"NVIDIA NIM call failed: {e}")
        raise


def generate(prompt: str, model_id: str, agent: str = "default") -> str:
    """Route to the correct provider based on model_id."""
    logger.info(f"generate() → model_id={model_id}, agent={agent}")

    # ── Local transformer models ──────────────────────────────────────────────
    if local_runner.is_available(model_id):
        if model_id == "local:dan-qwen":
            system = DAN_SYSTEM_PROMPT
        elif model_id == "local:qwen3-cyber":
            system = CYBER_LORA_SYSTEM_PROMPT
        else:
            system = SYSTEM_PROMPTS.get(agent, "You are a helpful AI assistant.")
        logger.info(f"Running local model: {model_id} | system prompt length={len(system)}")
        return local_runner.generate_local(
            model_id=model_id,
            system_prompt=system,
            user_prompt=prompt,
        )
    # ── Cloud / remote models ─────────────────────────────────────────────────
    elif model_id == "local:ollama":
        return call_ollama(prompt, agent)
    elif model_id == "api:gpt":
        return call_openai(prompt, agent)
    elif model_id == "api:gemini":
        return call_gemini(prompt, agent)
    elif model_id == "api:nvidia":
        return call_nvidia_gemma(prompt, agent)
    else:
        # Default and 'api:hf' → HuggingFace Router
        return call_huggingface(prompt, agent)


def list_models():
    return [
        {"id": "api:hf",           "name": "HuggingFace (Qwen-72B)",         "provider": "huggingface",  "is_local": False},
        {"id": "api:nvidia",       "name": "Gemma-4 31B (NVIDIA NIM)",       "provider": "nvidia",       "is_local": False},
        {"id": "local:qwen3-cyber","name": "Qwen3-14B Cyber LoRA (Local)",   "provider": "peft",         "is_local": True},
        {"id": "local:dan-qwen",   "name": "DAN-Qwen3 1.7B (Local)",         "provider": "transformers", "is_local": True},
        {"id": "local:ollama",     "name": "Ollama (Local)",                 "provider": "ollama",       "is_local": True},
        {"id": "api:gpt",          "name": "OpenAI GPT-4o-mini",             "provider": "openai",       "is_local": False},
        {"id": "api:gemini",       "name": "Google Gemini 2.0 Flash",        "provider": "gemini",       "is_local": False},
    ]
