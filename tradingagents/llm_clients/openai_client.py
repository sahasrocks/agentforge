from langchain_openai import ChatOpenAI
from .base_client import BaseLLMClient
from .capabilities import get_capabilities

# Base URLs for OpenAI-compatible providers
_BASE_URLS: dict[str, str] = {
    "xai":        "https://api.x.ai/v1",
    "deepseek":   "https://api.deepseek.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


class OpenAIClient(BaseLLMClient):
    """Handles OpenAI and all OpenAI-compatible providers (xai, deepseek, openrouter)."""

    def __init__(self, provider: str, model: str, base_url: str | None = None, **kwargs):
        self.model = model
        self.capabilities = get_capabilities(model)
        resolved_url = base_url or _BASE_URLS.get(provider)
        self._llm = ChatOpenAI(model=model, base_url=resolved_url, **kwargs)

    def get_llm(self) -> ChatOpenAI:
        return self._llm
