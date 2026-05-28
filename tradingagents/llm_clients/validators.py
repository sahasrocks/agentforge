from .model_catalog import MODEL_CATALOG, get_all_providers


def validate_provider(provider: str) -> None:
    if provider not in get_all_providers():
        supported = ", ".join(get_all_providers())
        raise ValueError(f"Unsupported provider '{provider}'. Choose from: {supported}")


def validate_model(provider: str, model: str) -> None:
    """Validate model name. Open-catalog providers (ollama, openrouter) accept any name."""
    catalog = MODEL_CATALOG.get(provider, [])
    if catalog and model not in catalog:
        supported = ", ".join(catalog)
        raise ValueError(
            f"Model '{model}' not in catalog for provider '{provider}'. "
            f"Supported: {supported}"
        )
