"""LLM Client abstraction for different backends."""

from abc import ABC, abstractmethod
from typing import Optional, Any

from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_core.language_models import BaseChatModel

from security_llm_lab.config import LLMConfig


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def get_chat_model(self) -> BaseChatModel:
        """Return a LangChain ChatModel."""
        pass


class OllamaClient(LLMClient):
    """Client for Ollama backend."""

    def __init__(self, config: LLMConfig):
        self.model_name = config.model_name
        self.base_url = config.base_url or "http://localhost:11434"

    def get_chat_model(self) -> BaseChatModel:
        return ChatOllama(
            model=self.model_name,
            base_url=self.base_url,
            temperature=0.1,
        )


class HuggingFaceClient(LLMClient):
    """Client for Hugging Face backend (Placeholder for now)."""

    def __init__(self, config: LLMConfig):
        self.model_name = config.model_name

    def get_chat_model(self) -> BaseChatModel:
        # TODO: Implement HuggingFace pipeline wrapper for LangChain
        # For now, raise NotImplementedError or return a mock
        raise NotImplementedError("HuggingFace backend not yet fully implemented for Agentic workflow.")


def get_llm_client(config: LLMConfig) -> LLMClient:
    """Factory function to get the appropriate LLM client."""
    if config.backend == "ollama":
        return OllamaClient(config)
    elif config.backend == "huggingface":
        return HuggingFaceClient(config)
    else:
        raise ValueError(f"Unsupported LLM backend: {config.backend}")
