from .base_client import BaseLLMClient
from .api_key_env import ensure_api_key
from .validators import validate_provider


def create_llm_client(
    provider: str,
    model: str,
    base_url: str | None = None,
    **kwargs,
) -> BaseLLMClient:
    """Return a provider-specific LLM client.

    Uses lazy imports so only the selected provider's SDK is loaded.
    Call .get_llm() on the result to obtain the LangChain BaseChatModel.
    """
    validate_provider(provider)
    ensure_api_key(provider)

    match provider:
        case "openai" | "xai" | "deepseek" | "openrouter":
            from .openai_client import OpenAIClient
            return OpenAIClient(provider, model, base_url, **kwargs)

        case "anthropic":
            from .anthropic_client import AnthropicClient
            return AnthropicClient(model, **kwargs)

        case "google":
            from .google_client import GoogleClient
            return GoogleClient(model, **kwargs)

        case "groq":
            from .groq_client import GroqClient
            return GroqClient(model, **kwargs)

        case "ollama":
            from .ollama_client import OllamaClient
            return OllamaClient(model, base_url or "http://localhost:11434", **kwargs)

        case _:
            # Should never reach here after validate_provider, but kept for safety
            raise ValueError(f"Unsupported provider: '{provider}'")
