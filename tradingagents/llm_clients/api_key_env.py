import os


# Maps provider key → environment variable name that holds the API key.
# None means no key is required (e.g. Ollama runs locally).
PROVIDER_API_KEY_ENV: dict[str, str | None] = {
    "openai":     "OPENAI_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
    "google":     "GOOGLE_API_KEY",
    "groq":       "GROQ_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "xai":        "XAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "ollama":     None,
}


def get_api_key_env(provider: str) -> str | None:
    """Return the env var name for a provider's API key, or None if not needed."""
    return PROVIDER_API_KEY_ENV.get(provider)


def ensure_api_key(provider: str) -> None:
    """Raise clearly if a required API key is missing from the environment."""
    env_var = get_api_key_env(provider)
    if env_var is None:
        return  # no key needed (Ollama)
    if not os.environ.get(env_var):
        raise EnvironmentError(
            f"Missing API key for provider '{provider}'. "
            f"Set the {env_var} environment variable in your .env file."
        )
