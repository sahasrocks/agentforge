from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_stocktwits_sentiment_tool(ticker: str, limit: int = 30) -> str:
    """Fetch recent StockTwits messages with Bullish/Bearish/Neutral labels for a ticker.
    Returns the latest retail trader messages sorted by recency."""
    return route_to_vendor("get_stocktwits_sentiment", ticker, limit)


@tool
def get_google_trends_tool(ticker: str, look_back_days: int = 30) -> str:
    """Get Google Search interest trend for a ticker over the past N days (0-100 scale).
    Rising search interest often precedes increased retail activity and volatility."""
    return route_to_vendor("get_google_trends", ticker, look_back_days)


@tool
def get_fear_greed_tool(curr_date: str) -> str:
    """Fetch the CNN Money Fear & Greed Index (stocks) and Alternative.me index (crypto).
    Score 0-100: Extreme Fear=0, Neutral=50, Extreme Greed=100.
    Useful for gauging broad market risk appetite and contrarian signals."""
    return route_to_vendor("get_fear_greed", curr_date)
