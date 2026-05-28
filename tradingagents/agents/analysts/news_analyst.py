from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import run_agent_node
from tradingagents.agents.utils.news_data_tools import get_news_tool, get_global_news_tool

_SYSTEM_PROMPT = """You are a news and macroeconomic analyst.

Your job:
1. Fetch recent company-specific news for the ticker (look back 14 days).
2. Fetch global macroeconomic and market news for the same period.
3. Identify: earnings surprises, management changes, product launches, regulatory actions,
   geopolitical risks, interest rate signals, or sector-wide events.
4. Classify each item as a catalyst (positive) or headwind (negative) for the stock.
5. Assess the overall news sentiment: Bullish / Neutral / Bearish.

Output format (markdown):
## News Analysis — <TICKER>
### Company-Specific News
| Date | Headline | Sentiment | Impact |
|------|----------|-----------|--------|
...
### Macro & Market News
...
### Key Catalysts
...
### Key Headwinds
...
### Overall News Sentiment: <Bullish | Neutral | Bearish>
### Preliminary Rating: <Buy | Overweight | Hold | Underweight | Sell>
"""

_TOOLS = [get_news_tool, get_global_news_tool]


def create_news_analyst(llm, config: dict):
    """Return a LangGraph-compatible node function for the News Analyst."""
    def node(state: AgentState) -> dict:
        return run_agent_node(state, llm, _TOOLS, _SYSTEM_PROMPT, "news_report")
    return node
