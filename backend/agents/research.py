# backend/agents/research.py
from backend.agents.base import BaseAgent
from backend.models import model_provider
import logging

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    async def process(self, prompt: str, model_name: str) -> str:
        logger.info(f"ResearchAgent → model={model_name}")
        effective_model = model_name if model_name in ("local:ollama", "api:gpt", "api:gemini") else "api:hf"
        return model_provider.generate(prompt, effective_model, agent="research")
