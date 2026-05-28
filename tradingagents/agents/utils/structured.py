import logging
from typing import Callable, TypeVar
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

def invoke_structured_or_freetext(
    structured_llm: BaseChatModel,   # llm.with_structured_output(Schema) already bound
    plain_llm: BaseChatModel,        # same llm without structured output binding
    prompt: list,                    # the messages list to send
    render: Callable[[T], str],      # converts the Pydantic instance → markdown string
    agent_name: str,                 # for logging only
) -> str:
    """Run the structured call and render to markdown; fall back to free-text on any failure.

    ``prompt`` is whatever the underlying LLM accepts (a string for chat
    invocations, a list of message dicts for chat models that take that
    shape). The same value is forwarded to the free-text path so the
    fallback sees the same input the structured call did.
    """
    if structured_llm is not None:
        try:
            result = structured_llm.invoke(prompt)
            return render(result)
        except Exception as exc:
            logger.warning(
                "%s: structured-output invocation failed (%s); retrying once as free text",
                agent_name, exc,
            )

    response = plain_llm.invoke(prompt)
    content = response.content
    # Some providers (OpenAI Responses API, Gemini 3.x) return content as a
    # list of typed blocks rather than a plain string — flatten to text.
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
            if not isinstance(block, dict) or block.get("type") == "text"
        )
    return content

def bind_structured(llm: BaseChatModel, schema: type[T]) -> BaseChatModel:
    """Return llm with structured output bound to schema."""
    return llm.with_structured_output(schema)
            