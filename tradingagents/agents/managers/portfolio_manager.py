from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.schemas import PortfolioDecision
from tradingagents.agents.utils.structured import invoke_structured_or_freetext, bind_structured

_SYSTEM_PROMPT = """You are the Portfolio Manager — the final decision-maker in this investment process.

You have read:
1. The Research Manager's investment plan (output of the bull vs bear debate).
2. The Trader's concrete trade proposal.
3. The full risk management debate between the Aggressive, Conservative, and Neutral analysts.

Your job:
1. Weigh all inputs and make THE FINAL investment decision — it will be acted upon.
2. Assign the definitive 5-tier portfolio rating: Buy / Overweight / Hold / Underweight / Sell.
3. Write a clear executive summary (2-3 sentences) suitable for a stakeholder briefing.
4. State the core investment thesis that won.
5. Set a price target (12-month) if applicable, or NAV target for mutual funds.
6. List the top 2-3 risk factors that could invalidate the thesis.
7. Specify the recommended time horizon.

You are accountable for this decision. Be clear, be specific, and be decisive.
"""


def _render_decision(decision: PortfolioDecision) -> str:
    lines = [
        "## Final Portfolio Decision",
        "",
        f"**Rating:** {decision.rating.value}",
        "",
        f"**Executive Summary:**\n{decision.executive_summary}",
        "",
        f"**Investment Thesis:**\n{decision.investment_thesis}",
    ]
    if decision.price_target is not None:
        lines += ["", f"**Price Target:** {decision.price_target}"]
    if decision.time_horizon:
        lines += ["", f"**Time Horizon:** {decision.time_horizon}"]
    if decision.risk_factors:
        lines += ["", f"**Key Risk Factors:**\n{decision.risk_factors}"]
    return "\n".join(lines)


def create_portfolio_manager(llm, config: dict):
    """Return a LangGraph-compatible node for the Portfolio Manager (final decision)."""

    structured_llm = bind_structured(llm, PortfolioDecision)

    def node(state: AgentState) -> dict:
        investment_plan = state.get("investment_plan", "")
        trader_plan     = state.get("trader_investment_plan", "")
        risk_debate     = state.get("risk_debate_state", {})
        risk_history    = risk_debate.get("history", "").strip()
        ticker          = state.get("company_of_interest", "the asset")
        trade_date      = state.get("trade_date", "")
        asset_type      = state.get("asset_type", "stock")

        sections = [
            f"Asset: **{ticker}**  |  Type: {asset_type}  |  Date: {trade_date}",
            "",
            "--- Research Investment Plan ---",
            investment_plan or "Not provided.",
            "",
            "--- Trader's Proposal ---",
            trader_plan or "Not provided.",
            "",
            "--- Risk Management Debate ---",
            risk_history or "No risk debate recorded.",
            "",
            "Make your final portfolio decision now.",
        ]

        prompt = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content="\n".join(sections)),
        ]

        final_decision = invoke_structured_or_freetext(
            structured_llm=structured_llm,
            plain_llm=llm,
            prompt=prompt,
            render=_render_decision,
            agent_name="PortfolioManager",
        )

        return {
            "risk_debate_state": {**risk_debate, "judge_decision": final_decision},
            "final_trade_decision": final_decision,
        }

    return node
