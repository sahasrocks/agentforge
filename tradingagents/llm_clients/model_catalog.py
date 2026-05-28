# Model options shown in the CLI dropdown per provider.
# Ollama and OpenRouter are open catalogs — user types the model name directly.
MODEL_CATALOG: dict[str, list[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "o1",
        "o1-mini",
        "o3-mini",
    ],
    "anthropic": [
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ],
    "google": [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-reasoner",
    ],
    "xai": [
        "grok-3",
        "grok-3-mini",
        "grok-2",
    ],
    "openrouter": [],   # open catalog — user supplies model name
    "ollama":     [],   # open catalog — depends on locally pulled models
}


def get_models_for_provider(provider: str) -> list[str]:
    return MODEL_CATALOG.get(provider, [])


def get_all_providers() -> list[str]:
    return list(MODEL_CATALOG.keys())
