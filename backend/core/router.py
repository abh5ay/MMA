# backend/core/router.py
"""AI Router – decides which agent and model to use and returns a response.
For now this is a simple stub that forwards to the appropriate agent class.
"""
import logging
from typing import Dict

from backend.agents.development import DevelopmentAgent
from backend.agents.cybersecurity import CybersecurityAgent
from backend.agents.research import ResearchAgent

logger = logging.getLogger(__name__)

class AirotorRouter:
    """Singleton router handling incoming requests.
    In a full implementation this would contain intent detection, model selection,
    tool orchestration, memory access, etc.
    """

    def __init__(self):
        self.agents: Dict[str, object] = {
            "development": DevelopmentAgent(),
            "cybersecurity": CybersecurityAgent(),
            "research": ResearchAgent(),
        }
        logger.info("AirotorRouter initialized with agents: %s", list(self.agents.keys()))

    async def handle_request(self, agent_name: str, model_name: str, prompt: str) -> str:
        """Route the request to the appropriate agent.
        Parameters
        ----------
        agent_name: str – one of 'development', 'cybersecurity', 'research'
        model_name: str – identifier for the model (e.g., 'local:ollama')
        prompt: str – user prompt
        Returns
        -------
        str – response text (stub for now)
        """
        agent = self.agents.get(agent_name.lower())
        if not agent:
            logger.error("Agent not found: %s", agent_name)
            raise ValueError(f"Unknown agent: {agent_name}")
        # In a real system we would select the model via ModelProvider
        logger.info("Routing to %s agent with model %s", agent_name, model_name)
        response = await agent.process(prompt, model_name)
        return response