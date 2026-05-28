from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.schemas import ResearchPlan
from tradingagents.agents.utils.structured import invoke_structured_or_freetext, bind_structured

_SYSTEM_PROMPT = """You are the Research Manager — the neutral judge of the bull vs bear investment debate.

Your job:
1. Read the full debate transcript between the bull and bear researchers.
2. Weigh the evidence on both sides objectively.
3. Identify which side made stronger, more data-backed arguments.
4. Produce a final investment plan with:
   - A 5-tier rating: Buy / Overweight / Hold / Underweight / Sell
   - A clear rationale citing the strongest evidence from both sides
   - Strategic actions: price levels, catalysts to watch, or exit conditions

Be decisive. Do not hedge into "Hold" just to avoid conflict — if the evidence leans
clearly to one side, reflect that in your rating.
"""


def _render_plan(plan: ResearchPlan) -> str:
    return (
        f"## Investment Plan\n\n"
        f"**Rating:** {plan.recommendation.value}\n\n"
        f"**Rationale:**\n{plan.rationale}\n\n"
        f"**Strategic Actions:**\n{plan.strategic_actions}"
    )


def create_research_manager(llm, config: dict):
    """Return a LangGraph-compatible node for the Research Manager (debate judge)."""

    structured_llm = bind_structured(llm, ResearchPlan)

    def node(state: AgentState) -> dict:
        debate  = state.get("investment_debate_state", {})
        history = debate.get("history", "").strip()
        ticker  = state.get("company_of_interest", "the asset")

        if not history:
            history = "No debate was recorded."

        prompt = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Asset under review: **{ticker}**\n\n"
                f"--- Full Debate Transcript ---\n{history}\n\n"
                "Based on the debate above, produce your final investment plan."
            )),
        ]

        investment_plan = invoke_structured_or_freetext(
            structured_llm=structured_llm,
            plain_llm=llm,
            prompt=prompt,
            render=_render_plan,
            agent_name="ResearchManager",
        )

        return {
            "investment_debate_state": {**debate, "judge_decision": investment_plan},
            "investment_plan": investment_plan,
        }

    return node
