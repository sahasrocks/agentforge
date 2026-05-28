from dataclasses import dataclass


@dataclass(frozen=True)
class ModelCapabilities:
    supports_tool_choice: bool
    supports_json_mode: bool
    supports_json_schema: bool
    preferred_structured_method: str        # "function_calling" | "json_mode" | "json_schema" | "none"
    requires_reasoning_content_roundtrip: bool  # DeepSeek thinking tokens
    requires_reasoning_split: bool              # models that split reasoning from response


# ── Registry ──────────────────────────────────────────────────────────────────
_FC   = "function_calling"
_JM   = "json_mode"
_JS   = "json_schema"
_NONE = "none"

CAPABILITIES: dict[str, ModelCapabilities] = {
    # OpenAI
    "gpt-4o":               ModelCapabilities(True,  True,  True,  _FC,   False, False),
    "gpt-4o-mini":          ModelCapabilities(True,  True,  True,  _FC,   False, False),
    "o1":                   ModelCapabilities(False, False, False, _NONE, False, False),
    "o1-mini":              ModelCapabilities(False, False, False, _NONE, False, False),
    "o3-mini":              ModelCapabilities(True,  False, True,  _FC,   False, False),

    # Anthropic
    "claude-opus-4-7":           ModelCapabilities(True, False, True, _FC, False, False),
    "claude-sonnet-4-6":         ModelCapabilities(True, False, True, _FC, False, False),
    "claude-haiku-4-5-20251001": ModelCapabilities(True, False, True, _FC, False, False),

    # Google
    "gemini-2.5-pro":       ModelCapabilities(True,  True,  True,  _FC,   False, False),
    "gemini-2.0-flash":     ModelCapabilities(True,  True,  True,  _FC,   False, False),
    "gemini-2.0-flash-lite":ModelCapabilities(True,  True,  True,  _FC,   False, False),

    # Groq
    "llama-3.3-70b-versatile": ModelCapabilities(True,  True,  False, _JM,   False, False),
    "llama-3.1-8b-instant":    ModelCapabilities(True,  True,  False, _JM,   False, False),
    "llama3-70b-8192":         ModelCapabilities(True,  True,  False, _JM,   False, False),
    "mixtral-8x7b-32768":      ModelCapabilities(True,  True,  False, _JM,   False, False),
    "gemma2-9b-it":            ModelCapabilities(False, True,  False, _JM,   False, False),

    # DeepSeek
    "deepseek-chat":        ModelCapabilities(True,  True,  False, _JM,   False, False),
    "deepseek-reasoner":    ModelCapabilities(False, False, False, _NONE, True,  False),

    # xAI
    "grok-3":               ModelCapabilities(True,  True,  True,  _FC,   False, False),
    "grok-3-mini":          ModelCapabilities(True,  True,  True,  _FC,   False, False),
    "grok-2":               ModelCapabilities(True,  True,  False, _FC,   False, False),

    # Ollama (local — conservative defaults; override per model as needed)
    "llama3.2":             ModelCapabilities(True,  True,  False, _JM,   False, False),
    "llama3.1":             ModelCapabilities(True,  True,  False, _JM,   False, False),
    "mistral":              ModelCapabilities(False, False, False, _NONE, False, False),
    "phi4":                 ModelCapabilities(True,  True,  False, _JM,   False, False),
    "qwen2.5":              ModelCapabilities(True,  True,  False, _JM,   False, False),
}

DEFAULT_CAPABILITIES = ModelCapabilities(
    supports_tool_choice=False,
    supports_json_mode=False,
    supports_json_schema=False,
    preferred_structured_method="none",
    requires_reasoning_content_roundtrip=False,
    requires_reasoning_split=False,
)


def get_capabilities(model: str) -> ModelCapabilities:
    """Exact match first, then prefix match, then safe default."""
    if model in CAPABILITIES:
        return CAPABILITIES[model]
    for key in CAPABILITIES:
        if model.startswith(key):
            return CAPABILITIES[key]
    return DEFAULT_CAPABILITIES
