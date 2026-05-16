# backend/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat, upload, tools, health, chat_stream, train
from backend.utils.logger import get_logger

app = FastAPI(title="MultiModelAI Backend", version="0.1.0")

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router,        prefix="/chat",   tags=["Chat"])
app.include_router(chat_stream.router,  prefix="/chat",   tags=["Chat Stream"])
app.include_router(upload.router,       prefix="/upload", tags=["Upload"])
app.include_router(tools.router,        prefix="/tools",  tags=["Tools"])
app.include_router(health.router,       prefix="/health", tags=["Health"])
app.include_router(train.router,        tags=["Train"])

logger = get_logger(__name__)

@app.get("/", summary="Root health check")
async def root():
    logger.info("Root endpoint called")
    return {"message": "MultiModelAI backend is running"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)