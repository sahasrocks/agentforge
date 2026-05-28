from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import run_agent_node
from tradingagents.agents.utils.fund_tools import (
    get_fund_nav_history_tool,
    get_fund_info_tool,
    get_trailing_returns_tool,
)

_SYSTEM_PROMPT = """You are a mutual fund NAV and performance analyst specialising in Indian funds.

Your job:
1. Fetch fund metadata: name, AMC, category, scheme type.
2. Fetch 1-year NAV history and describe the trend (uptrend / flat / downtrend).
3. Calculate trailing returns across 1M, 3M, 6M, 1Y, 3Y, 5Y vs the declared benchmark.
4. Assess whether the fund is consistently outperforming, in-line with, or underperforming
   its benchmark over multiple horizons.
5. Note any significant drawdowns or recovery patterns in NAV history.

Output format (markdown):
## Holdings Analysis — <SCHEME_CODE>
### Fund Profile
- Name / AMC / Category / Type: ...
### NAV Trend (1 Year)
...
### Trailing Returns vs Benchmark
| Period | Fund | Benchmark | Alpha |
|--------|------|-----------|-------|
...
### Consistency Assessment
...
### Drawdown & Recovery
...
### Preliminary Rating: <Buy | Overweight | Hold | Underweight | Sell>
"""

_TOOLS = [get_fund_nav_history_tool, get_fund_info_tool, get_trailing_returns_tool]


def create_holdings_analyst(llm, config: dict):
    """Return a LangGraph-compatible node function for the Holdings Analyst (mutual funds)."""
    def node(state: AgentState) -> dict:
        if state.get("asset_type") != "mutual_fund":
            return {"holdings_report": "N/A — asset is not a mutual fund."}
        return run_agent_node(state, llm, _TOOLS, _SYSTEM_PROMPT, "holdings_report")
    return node
