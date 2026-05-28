from langchain_anthropic import ChatAnthropic
from .base_client import BaseLLMClient
from .capabilities import get_capabilities


class AnthropicClient(BaseLLMClient):

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.capabilities = get_capabilities(model)
        self._llm = ChatAnthropic(model=model, **kwargs)

    def get_llm(self) -> ChatAnthropic:
        return self._llm
