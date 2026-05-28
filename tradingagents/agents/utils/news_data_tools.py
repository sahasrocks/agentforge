from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_news_tool(ticker: str, start_date: str, end_date: str) -> str:
    """Fetch recent news articles for a specific stock ticker between two dates.
    Dates must be in YYYY-MM-DD format. Returns headlines with sentiment labels."""
    return route_to_vendor("get_news", ticker, start_date, end_date)


@tool
def get_global_news_tool(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 10,
) -> str:
    """Fetch global macroeconomic and financial market news.
    curr_date must be YYYY-MM-DD. look_back_days controls the lookback window.
    limit caps the number of articles returned."""
    return route_to_vendor("get_global_news", curr_date, look_back_days, limit)


@tool
def get_reddit_sentiment_tool(ticker: str, limit: int = 25) -> str:
    """Fetch recent Reddit posts mentioning a stock ticker from r/wallstreetbets,
    r/investing, and r/stocks. Posts are sorted by score (upvotes) descending.
    limit caps the total posts returned across all subreddits."""
    return route_to_vendor("get_reddit_sentiment", ticker, limit)
