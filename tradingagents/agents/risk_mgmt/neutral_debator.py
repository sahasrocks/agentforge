from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState

_SYSTEM_PROMPT = """You are the Neutral Risk Analyst in a three-way risk management debate.

Your philosophy: balance is not weakness. You synthesise the aggressive and conservative
positions into a pragmatic middle ground that the Portfolio Manager can actually execute.
You are a moderating force, not a pushover — you will side with aggressive if the evidence
strongly supports it, and with conservative if the downside is genuinely asymmetric.

Your job in each round:
1. Read the trader's proposal and the full risk debate so far.
2. Identify the strongest points from BOTH the aggressive and conservative analysts.
3. Propose a BALANCED position: position size between the two extremes, entry conditions
   that satisfy both risk tolerance thresholds, and a reasonable stop loss.
4. Call out any logical gaps or unsupported claims from either side.

Rules:
- Be specific: always end with a concrete position sizing recommendation.
- Keep arguments to 3-4 focused points.
- End with your recommended balanced adjustment to the trader's proposal.
"""


def create_neutral_debator(llm, config: dict):
    """Return a LangGraph-compatible node for the Neutral Risk Debator."""

    def node(state: AgentState) -> dict:
        debate          = state.get("risk_debate_state", {})
        trader_plan     = state.get("trader_investment_plan", "No trader plan provided.")
        ticker          = state.get("company_of_interest", "the asset")
        round_count     = debate.get("count", 0)
        debate_history  = debate.get("history", "").strip()
        neu_history     = debate.get("neutral_history", "").strip()

        human_parts = [
            f"Asset: **{ticker}**\n",
            "--- Trader's Proposal ---",
            trader_plan,
        ]
        if debate_history:
            human_parts += ["\n--- Risk Debate So Far ---", debate_history]
        human_parts.append("\nProvide your balanced synthesis now.")

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

        new_neu_history = (neu_history + "\n\n" + content).strip()
        new_history     = (debate_history + f"\n\n[Neutral Round {round_count // 3 + 1}]\n{content}").strip()

        return {
            "risk_debate_state": {
                **debate,
                "neutral_history":          new_neu_history,
                "current_neutral_response": content,
                "history":                  new_history,
                "latest_speaker":           "Neutral",
                "count":                    round_count + 1,
            }
        }

    return node
