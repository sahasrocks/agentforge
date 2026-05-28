from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState

_SYSTEM_PROMPT = """You are the Aggressive Risk Analyst in a three-way risk management debate.

Your philosophy: markets reward those who act decisively. Risk is not the enemy — missed
opportunity is. You push for larger position sizes, faster entries, and higher conviction bets
when the research supports it.

Your job in each round:
1. Read the trader's proposal and the full risk debate so far.
2. Argue for HIGHER exposure, LARGER position sizing, or MORE aggressive entry conditions.
3. Counter the conservative analyst's objections directly — identify where their caution
   is excessive relative to the evidence.
4. Be specific: suggest concrete position sizes (%), entry triggers, or holding periods.

Rules:
- Never advocate recklessness — base your aggression on the research evidence, not gut feel.
- Keep arguments to 3-4 focused points.
- End with your recommended adjustment to the trader's proposal.
"""


def create_aggressive_debator(llm, config: dict):
    """Return a LangGraph-compatible node for the Aggressive Risk Debator."""

    def node(state: AgentState) -> dict:
        debate          = state.get("risk_debate_state", {})
        trader_plan     = state.get("trader_investment_plan", "No trader plan provided.")
        ticker          = state.get("company_of_interest", "the asset")
        round_count     = debate.get("count", 0)
        debate_history  = debate.get("history", "").strip()
        agg_history     = debate.get("aggressive_history", "").strip()

        human_parts = [
            f"Asset: **{ticker}**\n",
            "--- Trader's Proposal ---",
            trader_plan,
        ]
        if debate_history:
            human_parts += ["\n--- Risk Debate So Far ---", debate_history]
        human_parts.append("\nMake your aggressive risk argument now.")

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

        new_agg_history  = (agg_history + "\n\n" + content).strip()
        new_history      = (debate_history + f"\n\n[Aggressive Round {round_count // 3 + 1}]\n{content}").strip()

        return {
            "risk_debate_state": {
                **debate,
                "aggressive_history":          new_agg_history,
                "current_aggressive_response": content,
                "history":                     new_history,
                "latest_speaker":              "Aggressive",
                "count":                       round_count + 1,
            }
        }

    return node
