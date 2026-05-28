from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_stock_data_tool(symbol: str, start_date: str, end_date: str) -> str:
    """Fetch OHLCV (open, high, low, close, volume) price history for a stock ticker
    over a date range. Dates must be in YYYY-MM-DD format. Returns a CSV string."""
    return route_to_vendor("get_stock_data", symbol, start_date, end_date)
