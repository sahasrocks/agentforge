from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import run_agent_node
from tradingagents.agents.utils.fund_tools import (
    get_fund_by_category_tool,
    search_fund_tool,
)

_SYSTEM_PROMPT = """You are a mutual fund category and peer-comparison analyst.

Your job:
1. Fetch the fund's metadata to confirm its SEBI category.
2. List all peer funds in the same SEBI category using get_fund_by_category_tool.
3. Use search_fund_tool to look up 2-3 top-performing peers by name for comparison.
4. Assess how the target fund is positioned relative to peers:
   - Is it a large/mid/small player by AUM (if known)?
   - Does it have a differentiated strategy or is it a generic index-hugger?
5. Rate the category itself: is the SEBI category currently in favour or out of favour
   given macro conditions?

Output format (markdown):
## Category Analysis — <SCHEME_CODE>
### Category: <SEBI Category Name>
### Peer Landscape
Total funds in category: ...
Selected peers:
...
### Relative Positioning
...
### Category Outlook
- Macro tailwinds / headwinds for this category: ...
### Preliminary Rating: <Buy | Overweight | Hold | Underweight | Sell>
"""

_TOOLS = [get_fund_by_category_tool, search_fund_tool]


def create_category_analyst(llm, config: dict):
    """Return a LangGraph-compatible node function for the Category Analyst (mutual funds)."""
    def node(state: AgentState) -> dict:
        if state.get("asset_type") != "mutual_fund":
            return {"category_report": "N/A — asset is not a mutual fund."}
        return run_agent_node(state, llm, _TOOLS, _SYSTEM_PROMPT, "category_report")
    return node
