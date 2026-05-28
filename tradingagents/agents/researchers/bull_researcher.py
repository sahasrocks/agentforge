from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState

_SYSTEM_PROMPT = """You are a passionate bull-case investment researcher.

Your role in this debate is to argue as strongly as possible FOR investing in the asset.
Use specific evidence from the analyst reports provided. When a bear argument has been made,
directly counter it point by point — do not ignore the opposition.

Rules:
- Be specific: quote numbers, dates, and data from the reports.
- Acknowledge weaknesses briefly, then pivot to why the bull case still holds.
- Keep your argument focused: 3-5 key points maximum.
- End with a clear restatement of your rating recommendation.
- Do NOT repeat arguments already made in your own previous rounds verbatim — build on them.
"""


def _build_reports_block(state: AgentState) -> str:
    sections = []
    for key, label in [
        ("market_report",       "MARKET / TECHNICAL ANALYSIS"),
        ("fundamentals_report", "FUNDAMENTALS ANALYSIS"),
        ("news_report",         "NEWS ANALYSIS"),
        ("sentiment_report",    "SENTIMENT ANALYSIS"),
        ("holdings_report",     "FUND HOLDINGS ANALYSIS"),
        ("category_report",     "FUND CATEGORY ANALYSIS"),
    ]:
        content = state.get(key, "")
        if content and content != "N/A — asset is not a mutual fund.":
            sections.append(f"=== {label} ===\n{content}")
    return "\n\n".join(sections)


def create_bull_researcher(llm, config: dict):
    """Return a LangGraph-compatible node for the Bull Researcher debate participant."""

    def node(state: AgentState) -> dict:
        debate      = state.get("investment_debate_state", {})
        bear_prev   = debate.get("bear_history", "").strip()
        bull_prev   = debate.get("bull_history", "").strip()
        round_count = debate.get("count", 0)

        reports_block = _build_reports_block(state)
        ticker = state.get("company_of_interest", "the asset")

        human_parts = [
            f"You are arguing the bull case for: **{ticker}**\n",
            "--- Analyst Reports ---",
            reports_block,
        ]
        if bear_prev:
            human_parts += [
                "\n--- Bear's Previous Arguments ---",
                bear_prev,
                "\nCounter the bear's points and reinforce the bull thesis.",
            ]
        else:
            human_parts.append("\nMake your opening bull-case argument.")

        response = llm.invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content="\n".join(human_parts)),
        ])

        content = response.content
        if isinstance(content, list):
            content = "\n".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )

        new_bull_history = (bull_prev + "\n\n" + content).strip()
        new_history      = (debate.get("history", "") + f"\n\n[Bull Round {round_count // 2 + 1}]\n{content}").strip()

        return {
            "investment_debate_state": {
                **debate,
                "bull_history":     new_bull_history,
                "history":          new_history,
                "current_response": content,
                "count":            round_count + 1,
            }
        }

    return node
