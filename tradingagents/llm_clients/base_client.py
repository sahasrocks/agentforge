from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel


class BaseLLMClient(ABC):
    model: str
    capabilities: object

    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        """Return the underlying LangChain chat model."""
        ...

    @staticmethod
    def normalize_content(response) -> str:
        """Flatten list-of-blocks responses into a plain string.

        Handles providers that return content as typed block lists:
        OpenAI Responses API, Google Gemini 3.x.
        Text blocks are concatenated; reasoning/tool_use blocks are discarded.
        """
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "".join(parts)
        return str(content)
