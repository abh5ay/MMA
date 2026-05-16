# backend/routes/chat.py
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.core.agentic_runner import run_planning_phase, run_execution_phase, run_agent_loop
from backend.utils.logger import get_logger
import requests, json, os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

router = APIRouter()
logger = get_logger(__name__)

HF_KEY     = os.getenv("HUGGINGFACE_API_KEY", "")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")

AGENT_SYSTEM_PROMPTS = {
    "development": (
        "You are an expert autonomous software developer. "
        "You write clean, working code and always use absolute file paths. "
        "When the user mentions a location (Desktop, Downloads, a folder), you MUST use that exact path."
    ),
    "cybersecurity": (
        "You are a cybersecurity expert focused on defensive security, education, "
        "and ethical hacking labs. Help with security analysis, tool development, "
        "and vulnerability explanation."
    ),
    "research": (
        "You are an advanced research assistant. Help with summarizing papers, "
        "extracting knowledge, and providing well-structured, factual information."
    ),
}


class ChatRequest(BaseModel):
    agent:           str
    model:           str
    prompt:          str
    phase:           Optional[str]  = "auto"   # "auto" | "plan" | "execute"
    original_prompt: Optional[str]  = None     # used during execute phase


class StepItem(BaseModel):
    type:    str
    content: str
    tool:    Optional[str] = None


class ChatResponse(BaseModel):
    success:        bool
    response:       str
    steps:          Optional[List[StepItem]] = None
    needs_approval: Optional[bool]           = False
    plan_content:   Optional[str]            = None   # full text of implementation.md
    phase:          Optional[str]            = None
    usage:          Optional[Dict[str, Any]] = None


# ─── Model callers ────────────────────────────────────────────────────────────
def _call_hf(messages):
    headers = {"Authorization": f"Bearer {HF_KEY}", "Content-Type": "application/json"}
    payload = {"model": "Qwen/Qwen2.5-72B-Instruct", "messages": messages,
               "max_tokens": 2048, "temperature": 0.5}
    resp = requests.post("https://router.huggingface.co/v1/chat/completions",
                         headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _call_nvidia(messages):
    headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Accept": "text/event-stream",
               "Content-Type": "application/json"}
    payload = {"model": "google/gemma-4-31b-it", "messages": messages, "max_tokens": 4096,
               "temperature": 0.5, "top_p": 0.95, "stream": True,
               "chat_template_kwargs": {"enable_thinking": False}}
    response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
                             headers=headers, json=payload, stream=True, timeout=120)
    response.raise_for_status()
    full = ""
    for raw in response.iter_lines():
        if not raw: continue
        line = raw.decode("utf-8")
        if not line.startswith("data:"): continue
        data = line[5:].strip()
        if data == "[DONE]": break
        try:
            chunk = json.loads(data)
            full += chunk["choices"][0].get("delta", {}).get("content", "")
        except Exception:
            continue
    return full.strip()


def _make_caller(model_id: str):
    if model_id == "api:nvidia":
        return _call_nvidia
    return _call_hf


# ─── Endpoint ─────────────────────────────────────────────────────────────────
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest = Body(...)):
    try:
        logger.info(f"Chat: agent={request.agent}, model={request.model}, phase={request.phase}")

        is_agentic_model = request.model in ("api:hf", "api:nvidia")
        is_dev_agent     = request.agent == "development"
        system           = AGENT_SYSTEM_PROMPTS.get(request.agent, "You are a helpful AI assistant.")

        # ── Developer + agentic model → two-phase workflow ────────────────────
        if is_dev_agent and is_agentic_model and request.phase in ("auto", "plan"):
            caller = _make_caller(request.model)
            steps, plan_ready, plan_content = run_planning_phase(request.prompt, system, caller)

            step_items = [StepItem(**s) for s in steps]
            return ChatResponse(
                success        = True,
                response       = "✅ I've created a detailed **implementation plan**. Review it below, then approve to start execution.",
                steps          = step_items,
                plan_content   = plan_content,
                needs_approval = True,
                phase          = "plan",
            )

        # ── Developer execute phase (user approved) ───────────────────────────
        if is_dev_agent and is_agentic_model and request.phase == "execute":
            caller = _make_caller(request.model)
            prompt = request.original_prompt or request.prompt
            steps  = run_execution_phase(prompt, system, caller)

            final = next((s["content"] for s in reversed(steps) if s["type"] == "answer"), "Done.")
            return ChatResponse(
                success = True,
                response= final,
                steps   = [StepItem(**s) for s in steps],
                phase   = "execute",
            )

        # ── Other agents (cybersecurity, research) — unrestricted loop ────────
        if is_agentic_model and request.phase != "execute":
            caller = _make_caller(request.model)
            steps  = run_agent_loop(request.prompt, system, caller)
            final  = next((s["content"] for s in reversed(steps) if s["type"] == "answer"), "")
            return ChatResponse(success=True, response=final, steps=[StepItem(**s) for s in steps])

        # ── Simple (non-agentic model) ─────────────────────────────────────────
        from backend.models.model_provider import generate
        answer = generate(request.prompt, request.model, request.agent)
        return ChatResponse(success=True, response=answer)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))