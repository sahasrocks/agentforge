from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.schemas import TraderProposal
from tradingagents.agents.utils.structured import invoke_structured_or_freetext, bind_structured

_SYSTEM_PROMPT = """You are an experienced trader responsible for translating research into executable trade proposals.

You will receive a research investment plan (rating + rationale + strategic actions) produced
by the Research Manager after a bull vs bear debate.

Your job:
1. Accept or challenge the Research Manager's rating — you may adjust it one notch if execution
   reality warrants it (e.g. the plan is Buy but the stock just gapped up 10% today).
2. Propose a concrete trade action: Buy / Hold / Sell.
3. Suggest a realistic entry price (use recent price levels from the plan if mentioned).
4. Set a stop loss level — must be specific, not vague.
5. Recommend position sizing as a percentage of a hypothetical portfolio (e.g. "3% of portfolio").
6. Explain your reasoning in 2-3 sentences.

For mutual funds: entry price = current NAV, stop loss = NAV drawdown threshold (e.g. "exit if NAV
drops 8% from entry"), position sizing = SIP amount or lump-sum percentage.

Be decisive and specific. Vague proposals ("buy some if it dips") are not acceptable.
"""


def _render_proposal(proposal: TraderProposal) -> str:
    lines = [
        "## Trader Proposal",
        "",
        f"**Action:** {proposal.action.value}",
        f"**Reasoning:** {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        lines.append(f"**Entry Price:** {proposal.entry_price}")
    if proposal.stop_loss is not None:
        lines.append(f"**Stop Loss:** {proposal.stop_loss}")
    if proposal.position_sizing:
        lines.append(f"**Position Sizing:** {proposal.position_sizing}")
    return "\n".join(lines)


def create_trader(llm, config: dict):
    """Return a LangGraph-compatible node for the Trader agent."""

    structured_llm = bind_structured(llm, TraderProposal)

    def node(state: AgentState) -> dict:
        investment_plan = state.get("investment_plan", "No investment plan provided.")
        ticker          = state.get("company_of_interest", "the asset")
        trade_date      = state.get("trade_date", "")
        asset_type      = state.get("asset_type", "stock")

        prompt = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Asset: **{ticker}**  |  Type: {asset_type}  |  Date: {trade_date}\n\n"
                f"--- Research Investment Plan ---\n{investment_plan}\n\n"
                "Produce your trade proposal now."
            )),
        ]

        trader_plan = invoke_structured_or_freetext(
            structured_llm=structured_llm,
            plain_llm=llm,
            prompt=prompt,
            render=_render_proposal,
            agent_name="Trader",
        )

        return {"trader_investment_plan": trader_plan}

    return node
