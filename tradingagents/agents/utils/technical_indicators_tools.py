from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_technical_indicators_tool(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int = 30,
) -> str:
    """Calculate technical indicators for a stock ticker.

    Common indicator names: 'macd', 'rsi_14', 'boll' (Bollinger Bands),
    'close_20_sma', 'close_50_sma', 'atr', 'adx', 'cci', 'wr', 'stochrsi'.

    curr_date must be YYYY-MM-DD. look_back_days controls how many days of
    history to include (default 30).
    """
    return route_to_vendor("get_indicators", symbol, indicator, curr_date, look_back_days)
