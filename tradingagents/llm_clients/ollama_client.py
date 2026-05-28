from langchain_ollama import ChatOllama
from .base_client import BaseLLMClient
from .capabilities import get_capabilities


class OllamaClient(BaseLLMClient):

    def __init__(self, model: str, base_url: str = "http://localhost:11434", **kwargs):
        self.model = model
        self.capabilities = get_capabilities(model)
        self._llm = ChatOllama(model=model, base_url=base_url, **kwargs)

    def get_llm(self) -> ChatOllama:
        return self._llm
