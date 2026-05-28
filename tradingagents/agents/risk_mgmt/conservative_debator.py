from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState

_SYSTEM_PROMPT = """You are the Conservative Risk Analyst in a three-way risk management debate.

Your philosophy: capital preservation comes first. You focus on downside scenarios, tail risks,
and what happens when things go wrong — because they do go wrong. You prefer smaller initial
positions, clear stop losses, and staged entries over all-in bets.

Your job in each round:
1. Read the trader's proposal and the full risk debate so far.
2. Argue for LOWER exposure, TIGHTER stop losses, or MORE cautious entry conditions.
3. Counter the aggressive analyst's arguments — identify where overconfidence could lead to
   outsized losses.
4. Be specific: suggest concrete drawdown limits, position caps (%), or waiting conditions.

Rules:
- Never argue for paralysis — always provide an actionable, just-more-cautious alternative.
- Keep arguments to 3-4 focused points.
- End with your recommended adjustment to the trader's proposal.
"""


def create_conservative_debator(llm, config: dict):
    """Return a LangGraph-compatible node for the Conservative Risk Debator."""

    def node(state: AgentState) -> dict:
        debate          = state.get("risk_debate_state", {})
        trader_plan     = state.get("trader_investment_plan", "No trader plan provided.")
        ticker          = state.get("company_of_interest", "the asset")
        round_count     = debate.get("count", 0)
        debate_history  = debate.get("history", "").strip()
        con_history     = debate.get("conservative_history", "").strip()

        human_parts = [
            f"Asset: **{ticker}**\n",
            "--- Trader's Proposal ---",
            trader_plan,
        ]
        if debate_history:
            human_parts += ["\n--- Risk Debate So Far ---", debate_history]
        human_parts.append("\nMake your conservative risk argument now.")

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

        new_con_history = (con_history + "\n\n" + content).strip()
        new_history     = (debate_history + f"\n\n[Conservative Round {round_count // 3 + 1}]\n{content}").strip()

        return {
            "risk_debate_state": {
                **debate,
                "conservative_history":          new_con_history,
                "current_conservative_response": content,
                "history":                       new_history,
                "latest_speaker":                "Conservative",
                "count":                         round_count + 1,
            }
        }

    return node
