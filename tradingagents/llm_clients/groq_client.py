from langchain_groq import ChatGroq
from .base_client import BaseLLMClient
from .capabilities import get_capabilities


class GroqClient(BaseLLMClient):

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.capabilities = get_capabilities(model)
        self._llm = ChatGroq(model=model, **kwargs)

    def get_llm(self) -> ChatGroq:
        return self._llm
