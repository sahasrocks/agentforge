from langchain_google_genai import ChatGoogleGenerativeAI
from .base_client import BaseLLMClient
from .capabilities import get_capabilities


class GoogleClient(BaseLLMClient):

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.capabilities = get_capabilities(model)
        self._llm = ChatGoogleGenerativeAI(model=model, **kwargs)

    def get_llm(self) -> ChatGoogleGenerativeAI:
        return self._llm
