from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage


def _prefetch_all_tools(tools: list, state: dict) -> str:
    """Call every tool with best-effort args derived from state.

    Used as a fallback when the provider fails to generate valid tool calls
    (e.g. Groq/LLaMA malformed function-call syntax). Results are returned
    as a plain-text block for injection into the prompt.
    """
    ticker     = state.get("company_of_interest", "")
    trade_date = state.get("trade_date", "")

    try:
        end_dt    = datetime.strptime(trade_date, "%Y-%m-%d")
        start_dt  = end_dt - timedelta(days=30)
        start_date = start_dt.strftime("%Y-%m-%d")
    except Exception:
        start_date = trade_date

    # Mapping from common tool parameter names → values derived from state
    _ARG_MAP = {
        "ticker":         ticker,
        "symbol":         ticker,
        "scheme_code":    ticker,
        "query":          ticker,
        "start_date":     start_date,
        "end_date":       trade_date,
        "curr_date":      trade_date,
        "freq":           "quarterly",
        "benchmark_code": "^NSEI",
        "look_back_days": 30,
        "limit":          10,
    }

    sections = []
    for tool in tools:
        try:
            # Build kwargs from the tool's input schema field names
            schema = tool.args_schema
            if schema is not None:
                kwargs = {
                    field: _ARG_MAP[field]
                    for field in schema.model_fields
                    if field in _ARG_MAP
                }
            else:
                kwargs = {}

            result = tool.invoke(kwargs)
            sections.append(f"[{tool.name}]\n{result}")
        except Exception as exc:
            sections.append(f"[{tool.name}] Could not fetch data: {exc}")

    return "\n\n".join(sections) if sections else "No pre-fetched data available."


def _flatten_content(content) -> str:
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


def run_agent_node(
    state: dict,
    llm,
    tools: list,
    system_prompt: str,
    output_key: str,
) -> dict:
    """Generic tool-calling loop for analyst nodes.

    Binds tools to the LLM and runs the conversation until the model stops
    issuing tool calls, then returns {output_key: final_text}.

    If the provider cannot generate valid tool calls (Groq/LLaMA malformed
    syntax, missing tool-call support), falls back to pre-fetching all tools
    eagerly and injecting results as plain-text context.
    """
    llm_with_tools = llm.bind_tools(tools)
    tool_map       = {t.name: t for t in tools}

    ticker     = state.get("company_of_interest", "")
    trade_date = state.get("trade_date", "")
    asset_type = state.get("asset_type", "stock")
    past_ctx   = state.get("past_context", "")

    task_parts = [
        f"Asset: {ticker}  |  Type: {asset_type}  |  Analysis date: {trade_date}",
    ]
    if past_ctx:
        task_parts.append(f"\nPrior context from memory:\n{past_ctx}")
    task_parts.append("\nProduce your structured analysis report now.")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="\n".join(task_parts)),
    ]

    # ── Primary path: provider supports tool calling ───────────────────────────
    try:
        while True:
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for call in response.tool_calls:
                tool_fn = tool_map.get(call["name"])
                if tool_fn is None:
                    result = f"Tool '{call['name']}' not found."
                else:
                    try:
                        result = tool_fn.invoke(call["args"])
                    except Exception as exc:
                        result = f"Tool error: {exc}"

                messages.append(
                    ToolMessage(content=str(result), tool_call_id=call["id"])
                )

        return {output_key: _flatten_content(response.content)}

    except Exception:
        # ── Fallback path: pre-fetch tools, inject as text, call plain LLM ────
        pre_fetched = _prefetch_all_tools(tools, state)

        fallback_human = (
            "\n".join(task_parts)
            + f"\n\n--- Pre-fetched Tool Data ---\n{pre_fetched}\n\n"
            + "Using the data above, produce your structured analysis report."
        )
        fallback_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=fallback_human),
        ]
        fallback_response = llm.invoke(fallback_messages)
        return {output_key: _flatten_content(fallback_response.content)}
