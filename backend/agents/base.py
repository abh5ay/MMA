# backend/agents/base.py
"""Base class for all specialized agents.
Each concrete agent must implement an asynchronous ``process`` method that
receives the user ``prompt`` and the ``model_name`` selected by the router.
For now the implementation is a simple stub returning a canned response.
"""
import abc

class BaseAgent(abc.ABC):
    @abc.abstractmethod
    async def process(self, prompt: str, model_name: str) -> str:
        """Handle a prompt and return a response string.
        Args:
            prompt: The user message.
            model_name: Identifier of the model to use (e.g., ``local:ollama``).
        Returns:
            A response string.
        """
        raise NotImplementedError
