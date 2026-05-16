# backend/routes/chat_stream.py
"""
SSE streaming endpoint — emits tokens as they arrive from the model.
Events emitted:
  {"type": "plan_token",   "content": "..."}   - planning phase tokens
  {"type": "plan_ready",   "content": "..."}   - full plan text, show PlanCard
  {"type": "needs_approval"}                   - stop, wait for user
  {"type": "token",        "content": "..."}   - execution/response tokens
  {"type": "tool_call",    "tool": "...", "content": "..."} - tool about to run
  {"type": "tool_result",  "tool": "...", "content": "..."} - tool output
  {"type": "done"}                             - stream complete
  {"type": "error",        "content": "..."}   - error
"""
import json, os, re, threading, asyncio, logging
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

import requests as req

router  = APIRouter()
logger  = logging.getLogger(__name__)

HF_KEY       = os.getenv("HUGGINGFACE_API_KEY", "")
NVIDIA_KEY       = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MISTRAL_KEY = os.getenv("NVIDIA_MISTRAL_KEY", "")
XAI_KEY          = os.getenv("XAI_API_KEY", "")
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY", "")
CEREBRAS_KEY = os.getenv("CEREBRAS_API_KEY", "")

PLAN_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "agent_workspace", "implementation.md")
)
os.makedirs(os.path.dirname(PLAN_PATH), exist_ok=True)

# ─── Tool imports ─────────────────────────────────────────────────────────────
from backend.tools.code_runner import run_python, run_bash
from backend.tools.file_tools   import read_file, write_file, list_dir

TOOL_DISPATCH = {
    "run_python": run_python,
    "run_bash":   run_bash,
    "read_file":  read_file,
    "list_dir":   list_dir,
    "write_file": write_file,
}

TOOLS_DOC = """
You have TWO tools. Use ONE per message, EXACTLY in this format:
<tool>TOOL_NAME</tool><input>INPUT</input>

TOOL 1 — run_bash
  Use for: create directories, write files, install packages, download files
  Heredoc file writing (PREFERRED for all file writes):
    cat > /absolute/path/file.py << 'HEREDOC'
    file content here
    HEREDOC
  Directory creation: mkdir -p /abs/path/dir
  Install packages: pip install flask  OR  cd /path && npm install

  ★ DOWNLOADING IMAGES & ASSETS FROM THE INTERNET:
    Use curl to download any image, font, or asset file:
    curl -L -o /path/to/save/image.jpg "https://example.com/image.jpg"
    For multiple files:
    curl -L -o /path/hero1.jpg "https://..." && curl -L -o /path/hero2.jpg "https://..."
    ALWAYS download real images for projects — never use broken placeholder URLs.
    Use Unsplash for photos:  https://source.unsplash.com/400x300/?marvel,superhero
    Use Wikimedia/direct CDN links for specific content.

  ★ TRAINING ML MODELS:
    Download dataset: curl -L -o /path/data.csv "DATASET_URL"
    Install ML deps: pip install scikit-learn pandas numpy joblib
    Run training: python3 /path/train.py  (write the full training script first)
    Save model: use joblib.dump(model, '/path/model.pkl')

TOOL 2 — run_python
  Use ONLY for quick calculations you cannot do with bash.

RULES:
- ABSOLUTE paths always (e.g. /Users/abhaypratapsingh/Desktop/myproject/app.py)
- Prefer run_bash for EVERYTHING — it is the most reliable tool
- Download REAL images using curl — never use placeholder image services that return 404
- When ALL files are written, give your final summary (NO tool tag)
"""

PLANNING_PROMPT = """You are a pragmatic software architect. Your job is to write a MINIMAL, EXECUTABLE implementation plan.

⚡ SCOPE RULE — MATCH COMPLEXITY TO THE REQUEST:
- "make a [simple thing]" → 1-3 files max. Single-file preferred.
- "make a [full/complete/complex app]" → multi-file, but still minimal.
- NEVER add enterprise structure, sub-packages, or test suites unless explicitly asked.
- A "todo app" = ONE Python or HTML file. Not 10+ files with PyQt6, models, views, utils.

🧠 Think before writing:
1. What is the SIMPLEST correct implementation?
2. What is the MINIMUM number of files needed?
3. What technology requires the fewest files? (HTML/JS single file > Python multi-file)

Output format (markdown only, no preamble):

# Implementation Plan: [Name]

## 🎯 Project Overview
[1-2 sentences]

## 📁 File Structure
```
/Users/abhaypratapsingh/Desktop/[project-name]/
├── [file1]  — purpose
└── [file2]  — purpose (only if truly needed)
```

## 🛠️ Tech Stack
[brief, 1-2 lines]

## 📦 Dependencies
```
[only external packages, or "None"]
```

## 🚀 Build Steps
1. Create directory
2. Write [file1] — [what it contains]
3. (if needed) Write [file2]

## 💡 How to Run
[single command to run the app]
"""

EXECUTION_PROMPT = """
EXECUTION RULES — READ EVERY WORD:

1. ⚡ BATCH EVERYTHING INTO AS FEW TOOL CALLS AS POSSIBLE
   You have a MAXIMUM of 10 tool calls. USE AT MOST 2-3.
   - Call 1: ONE run_bash that does:
       a) mkdir -p for ALL directories
       b) writes ALL files using heredoc chained with newlines
   Example of a single bash call that creates 3 files:

     mkdir -p /Users/abhaypratapsingh/Desktop/myapp && \\
     cat > /Users/abhaypratapsingh/Desktop/myapp/app.py << 'EOF'
     print("hello")
     EOF
     cat > /Users/abhaypratapsingh/Desktop/myapp/style.css << 'EOF'
     body {{ color: red; }}
     EOF

   - Call 2 (only if needed): pip install / npm install
   - Call 3: STOP — write the final summary, no more tool calls

2. WRITE COMPLETE FILES — no truncation, no "# rest of code here"
   Every file must be 100% complete and working.

3. DO NOT run or launch the application
   No `python app.py`, no `npm start`, no `flask run`.

4. DO NOT re-check, re-run, or iterate
   Write once, completely, then STOP.

5. FINAL MESSAGE (after the last tool call)
   Output ONLY:
   ## ✅ Build Complete
   - /path/to/file1
   - /path/to/file2
   Run with: [exact command]
   Then STOP. No more tool calls.
"""

# Detect conversational/question messages that should skip planning
CONVERSATIONAL_STARTS = {
    'where', 'what', 'why', 'how', 'when', 'who', 'which', 'is', 'are',
    'did', 'does', 'was', 'were', 'tell', 'show', 'explain', 'describe',
    'list', 'give', 'can', 'could', 'would', 'should', 'do', 'have', 'has',
    'hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening'
}

def _is_conversational(prompt: str) -> bool:
    """True if message is a question/conversation, not a build request."""
    p = prompt.lower().strip()
    if p.endswith('?'): return True
    first = p.split()[0] if p.split() else ''
    return first in CONVERSATIONAL_STARTS

AGENT_PROMPTS = {
    "development": "You are an expert autonomous software developer. Always use absolute file paths.",
    "cybersecurity": "You are a cybersecurity expert focused on defensive security and ethical hacking.",
    "research": "You are an advanced research assistant providing well-structured, factual information.",
}


class StreamRequest(BaseModel):
    agent:           str
    model:           str
    prompt:          str
    phase:           Optional[str] = "auto"
    original_prompt: Optional[str] = None


# ─── Streaming model callers ──────────────────────────────────────────────────
def _stream_hf(messages):
    """Yields text tokens from HuggingFace streaming API."""
    headers = {"Authorization": f"Bearer {HF_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": messages,
        "max_tokens": 3000,
        "temperature": 0.5,
        "stream": True,
    }
    resp = req.post("https://router.huggingface.co/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _stream_nvidia(messages):
    """Yields text tokens from NVIDIA NIM streaming API."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemma-4-31b-it",
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.5,
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    resp = req.post("https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _stream_grok(messages):
    """Yields tokens from xAI Grok API (OpenAI-compatible)."""
    headers = {
        "Authorization": f"Bearer {XAI_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       "grok-3",
        "messages":    messages,
        "max_tokens":  4096,
        "temperature": 0.5,
        "stream":      True,
    }
    resp = req.post("https://api.x.ai/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _stream_gpt_oss(messages):
    """Yields tokens from openai/gpt-oss-120b via HuggingFace Inference API."""
    headers = {"Authorization": f"Bearer {HF_KEY}", "Content-Type": "application/json"}
    payload = {
        "model":       "openai/gpt-oss-120b",
        "messages":    messages,
        "max_tokens":  4096,
        "temperature": 0.5,
        "stream":      True,
    }
    resp = req.post("https://router.huggingface.co/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=180)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _stream_together(messages):
    """Yields tokens from Together AI (DeepSeek-Coder-33B or any Together model)."""
    headers = {
        "Authorization": f"Bearer {TOGETHER_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       "deepseek-ai/deepseek-coder-33b-instruct",
        "messages":    messages,
        "max_tokens":  4096,
        "temperature": 0.5,
        "stream":      True,
    }
    resp = req.post("https://api.together.xyz/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _stream_cerebras(messages):
    """Yields tokens from Cerebras AI (Llama-3.3-70B on Cerebras wafer chips — extremely fast)."""
    headers = {
        "Authorization": f"Bearer {CEREBRAS_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       "llama-3.3-70b",
        "messages":    messages,
        "max_tokens":  4096,
        "temperature": 0.5,
        "stream":      True,
    }
    resp = req.post("https://api.cerebras.ai/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _stream_nvidia_mistral(messages):
    """Yields text tokens from NVIDIA NIM streaming API for Mistral."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_MISTRAL_KEY}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistralai/mistral-medium-3.5-128b",
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 0.5,
        "stream": True,
    }
    resp = req.post("https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    for raw in resp.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            token = chunk["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token
        except Exception:
            continue


def _get_streamer(model_id: str):
    if model_id == "api:nvidia":          return _stream_nvidia
    if model_id == "api:nvidia-mistral":  return _stream_nvidia_mistral
    if model_id == "api:grok":            return _stream_grok
    if model_id == "api:gpt-oss":         return _stream_gpt_oss
    if model_id == "api:together":        return _stream_together
    if model_id == "api:cerebras":        return _stream_cerebras
    return _stream_hf   # default (api:hf + Qwen-72B)


def _extract_tool_call(text: str):
    m = re.search(r"<tool>(.*?)</tool>\s*<input>(.*?)</input>", text, re.DOTALL)
    return (m.group(1).strip(), m.group(2)) if m else None


# ─── Event generators (sync, run in thread) ──────────────────────────────────
def _events_planning(prompt: str, streamer) -> list:
    """Yields dicts for planning phase. Streams plan tokens, saves file, emits plan_ready."""
    messages = [
        {"role": "system", "content": PLANNING_PROMPT},
        {"role": "user",   "content": f"Create a comprehensive implementation plan for: {prompt}"},
    ]

    plan_text = ""
    for token in streamer(messages):
        plan_text += token
        yield {"type": "plan_token", "content": token}

    # Save plan
    try:
        with open(PLAN_PATH, "w") as f:
            f.write(plan_text)
    except Exception as e:
        logger.error(f"Failed to save plan: {e}")

    # Single combined event — avoids the second event being lost at stream chunk boundaries
    yield {"type": "plan_ready", "needs_approval": True}


def _events_execution(prompt: str, system: str, streamer, max_iter: int = 10):
    """Yields dicts for execution phase with tool calls."""
    plan_content = ""
    if os.path.exists(PLAN_PATH):
        try:
            with open(PLAN_PATH) as f:
                plan_content = f.read()
        except Exception:
            pass

    full_sys = system + "\n\n" + TOOLS_DOC + "\n\n" + EXECUTION_PROMPT
    messages = [
        {"role": "system",    "content": full_sys},
        {"role": "user",      "content": f"Original task: {prompt}"},
        {"role": "assistant", "content": f"Approved plan:\n\n{plan_content}"},
        {"role": "user",      "content": (
            "Execute the plan NOW using run_bash.\n"
            "Step 1: mkdir -p to create all directories at once.\n"
            "Step 2: use `cat > /path/file << 'HEREDOC' ... HEREDOC` for each file.\n"
            "Step 3: run `pip install` or `npm install` if needed.\n"
            "DO NOT run the app. DO NOT iterate. When all files exist → give ## ✅ Build Complete summary."
        )},
    ]

    for iteration in range(max_iter):
        full_response = ""

        for token in streamer(messages):
            full_response += token
            yield {"type": "token", "content": token}

        tool_call = _extract_tool_call(full_response)
        if tool_call is None:
            # Final answer — already streamed
            break

        name, inp = tool_call
        yield {"type": "tool_call", "tool": name, "content": inp}

        fn = TOOL_DISPATCH.get(name)
        result = fn(inp) if fn else f"ERROR: unknown tool '{name}'"
        yield {"type": "tool_result", "tool": name, "content": result}

        # Feed result back
        messages.append({"role": "assistant", "content": full_response})
        messages.append({"role": "user",      "content": f"<tool_result>{result}</tool_result>\nContinue."})
    else:
        yield {"type": "token", "content": "\n\n_(Reached max iterations)_"}


def _events_simple(prompt: str, system: str, streamer):
    """Non-agentic: just stream the response."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": prompt},
    ]
    for token in streamer(messages):
        yield {"type": "token", "content": token}


# ─── Main generator ───────────────────────────────────────────────────────────
def _all_events(request: StreamRequest):
    """Top-level sync generator combining all phases."""
    try:
        is_agentic_model = request.model in ("api:hf", "api:nvidia", "api:nvidia-mistral", "api:grok", "api:gpt-oss", "api:together", "api:cerebras")
        is_dev_agent     = request.agent == "development"
        system           = AGENT_PROMPTS.get(request.agent, "You are a helpful AI assistant.")
        streamer         = _get_streamer(request.model)
        phase            = request.phase or "auto"

        if is_dev_agent and is_agentic_model and phase in ("auto", "plan") and not _is_conversational(request.prompt):
            yield from _events_planning(request.prompt, streamer)

        elif is_dev_agent and is_agentic_model and phase == "execute":
            prompt = request.original_prompt or request.prompt
            yield from _events_execution(prompt, system, streamer)

        elif is_agentic_model:
            full_sys = system + "\n\n" + TOOLS_DOC
            messages = [
                {"role": "system", "content": full_sys},
                {"role": "user",   "content": request.prompt},
            ]
            full_response = ""
            for token in streamer(messages):
                full_response += token
                yield {"type": "token", "content": token}

        else:
            # Non-cloud model: fall back to non-streaming
            from backend.core.router import AirotorRouter
            airotor = AirotorRouter()
            import asyncio
            answer = asyncio.run(airotor.handle_request(request.agent, request.model, request.prompt))
            for ch in answer:
                yield {"type": "token", "content": ch}

        yield {"type": "done"}

    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        yield {"type": "error", "content": str(e)}


# ─── FastAPI endpoint ─────────────────────────────────────────────────────────
@router.post("/stream")
async def chat_stream(request: StreamRequest = Body(...)):
    loop = asyncio.get_event_loop()
    q    = asyncio.Queue()

    def producer():
        try:
            for event in _all_events(request):
                loop.call_soon_threadsafe(q.put_nowait, event)
        except Exception as e:
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)   # sentinel

    threading.Thread(target=producer, daemon=True).start()

    async def event_generator():
        while True:
            event = await q.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )
