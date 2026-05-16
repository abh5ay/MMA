# backend/routes/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Health check for the backend")
async def health_check():
    return {"status": "ok"}
