from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_fundamentals_tool(ticker: str, curr_date: str) -> str:
    """Fetch company fundamentals for a stock ticker: PE ratio, PB ratio, EV/EBITDA,
    profit margins, return on equity, debt-to-equity, dividend yield, analyst target
    price, 52-week high/low, and beta. curr_date must be YYYY-MM-DD."""
    return route_to_vendor("get_fundamentals", ticker, curr_date)


@tool
def get_balance_sheet_tool(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str = "",
) -> str:
    """Fetch the balance sheet for a stock ticker.
    freq must be 'quarterly' or 'annual'. curr_date is YYYY-MM-DD (used for context)."""
    return route_to_vendor("get_balance_sheet", ticker, freq, curr_date)


@tool
def get_cashflow_tool(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str = "",
) -> str:
    """Fetch the cash flow statement for a stock ticker showing operating, investing,
    and financing cash flows. freq must be 'quarterly' or 'annual'."""
    return route_to_vendor("get_cashflow", ticker, freq, curr_date)


@tool
def get_income_statement_tool(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str = "",
) -> str:
    """Fetch the income statement for a stock ticker: revenue, gross profit, EBITDA,
    operating income, and net income. freq must be 'quarterly' or 'annual'."""
    return route_to_vendor("get_income_statement", ticker, freq, curr_date)
