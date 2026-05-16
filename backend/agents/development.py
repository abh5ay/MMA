# backend/agents/development.py
from backend.agents.base import BaseAgent
from backend.models import model_provider
import logging

logger = logging.getLogger(__name__)

class DevelopmentAgent(BaseAgent):
    async def process(self, prompt: str, model_name: str) -> str:
        logger.info(f"DevelopmentAgent → model={model_name}")
        # If model is Ollama/local, forward directly; otherwise use HF coder model
        effective_model = model_name if model_name in ("local:ollama", "api:gpt", "api:gemini") else "api:hf"
        return model_provider.generate(prompt, effective_model, agent="development")
