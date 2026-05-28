from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import run_agent_node
from tradingagents.agents.utils.core_stock_tools import get_stock_data_tool
from tradingagents.agents.utils.technical_indicators_tools import get_technical_indicators_tool

_SYSTEM_PROMPT = """You are a quantitative market analyst specialising in technical analysis.

Your job:
1. Fetch 60 days of OHLCV price history for the given ticker.
2. Calculate key indicators: RSI-14, MACD, Bollinger Bands (boll), 20-day SMA, 50-day SMA, ATR.
3. Identify the primary trend (uptrend / downtrend / sideways).
4. Note key support and resistance levels.
5. Flag any momentum divergences or breakout signals.

Output format (markdown):
## Market Analysis — <TICKER>
### Trend: <Uptrend | Downtrend | Sideways>
### Key Levels
- Support: ...
- Resistance: ...
### Indicator Summary
- RSI-14: ...
- MACD: ...
- Bollinger Bands: ...
- 20/50 SMA: ...
### Signals & Observations
...
### Preliminary Rating: <Buy | Overweight | Hold | Underweight | Sell>
"""

_TOOLS = [get_stock_data_tool, get_technical_indicators_tool]


def create_market_analyst(llm, config: dict):
    """Return a LangGraph-compatible node function for the Market Analyst."""
    def node(state: AgentState) -> dict:
        return run_agent_node(state, llm, _TOOLS, _SYSTEM_PROMPT, "market_report")
    return node
