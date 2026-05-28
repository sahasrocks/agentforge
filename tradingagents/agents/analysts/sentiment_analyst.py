from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import run_agent_node
from tradingagents.agents.utils.news_data_tools import get_reddit_sentiment_tool
from tradingagents.agents.utils.sentiment_data_tools import (
    get_stocktwits_sentiment_tool,
    get_google_trends_tool,
    get_fear_greed_tool,
)

_SYSTEM_PROMPT = """You are a social media and retail sentiment analyst.

Your job — use ALL available tools:
1. Fetch Reddit posts (r/wallstreetbets, r/investing, r/stocks) via get_reddit_sentiment.
2. Fetch StockTwits messages (Bullish/Bearish labels) via get_stocktwits_sentiment.
3. Fetch Google Search interest trend via get_google_trends — rising interest signals growing retail attention.
4. Fetch the Fear & Greed Index via get_fear_greed — broad market risk appetite context.

Then synthesise:
- Overall retail mood: Bullish / Neutral / Bearish
- Any meme-stock dynamics, short-squeeze talk, or unusual options speculation
- Whether retail sentiment aligns with or diverges from fundamentals
- What the Fear & Greed reading means for this specific trade (contrarian or confirming)

Output format (markdown):
## Sentiment Analysis — <TICKER>
### Reddit Pulse
Top posts by upvote score: ...
### StockTwits Pulse
Bullish/Bearish breakdown: ...
### Google Trends
Search interest: Rising / Stable / Falling — implication: ...
### Market Fear & Greed
Score and label — contrarian or confirming signal: ...
### Tone Assessment
- Overall mood: <Bullish | Neutral | Bearish>
- Dominant themes: ...
### Risk Flags
- Meme dynamics: <Yes | No>
- Short-squeeze talk: <Yes | No>
- Options speculation: <Yes | No>
### Divergence from Fundamentals
...
### Retail Sentiment Score: <Strong Buy | Buy | Neutral | Sell | Strong Sell>
### Preliminary Rating: <Buy | Overweight | Hold | Underweight | Sell>
"""

_TOOLS = [
    get_reddit_sentiment_tool,
    get_stocktwits_sentiment_tool,
    get_google_trends_tool,
    get_fear_greed_tool,
]


def create_sentiment_analyst(llm, config: dict):
    """Return a LangGraph-compatible node function for the Sentiment Analyst."""
    def node(state: AgentState) -> dict:
        return run_agent_node(state, llm, _TOOLS, _SYSTEM_PROMPT, "sentiment_report")
    return node
