# backend/routes/tools.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.utils.logger import get_logger
import subprocess, shlex

router = APIRouter()
logger = get_logger(__name__)

class ToolRequest(BaseModel):
    tool: str  # e.g., 'git', 'terminal'
    args: list[str]

@router.post("/", summary="Execute a tool action (stub implementation)")
async def execute_tool(request: ToolRequest = Body(...)):
    try:
        logger.info(f"Executing tool: {request.tool} args: {request.args}")
        if request.tool == "terminal":
            # Simple command execution – dangerous in prod, stub only
            cmd = " ".join(shlex.quote(arg) for arg in request.args)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return {"success": True, "output": result.stdout + result.stderr}
        elif request.tool == "git":
            # Stub: just echo the args
            return {"success": True, "output": f"git command simulated: {' '.join(request.args)}"}
        else:
            raise ValueError("Unsupported tool")
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
