"""LLM Client abstraction for different backends."""

from abc import ABC, abstractmethod
from typing import Optional, Any

from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_core.language_models import BaseChatModel
import os

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


class OpenAIClient(LLMClient):
    """Client for OpenAI backend."""

    def __init__(self, config: LLMConfig):
        self.model_name = config.model_name
        self.api_key = os.getenv("OPENAI_API_KEY")

    def get_chat_model(self) -> BaseChatModel:
        return ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=self.api_key,
            temperature=0.1,
        )


def get_llm_client(config: LLMConfig) -> LLMClient:
    """Factory function to get the appropriate LLM client."""
    if config.backend == "ollama":
        return OllamaClient(config)
    elif config.backend == "openai":
        return OpenAIClient(config)
    else:
        raise ValueError(f"Unsupported LLM backend: {config.backend}")
