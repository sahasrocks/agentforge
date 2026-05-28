from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_fund_nav_history_tool(
    scheme_code: str,
    start_date: str,
    end_date: str,
) -> str:
    """Fetch historical NAV (Net Asset Value) for an Indian mutual fund scheme.
    scheme_code is the numeric MFApi scheme code (e.g. '119598').
    Dates must be in YYYY-MM-DD format. Returns a CSV of date and NAV."""
    return route_to_vendor("get_fund_nav_history", scheme_code, start_date, end_date)


@tool
def get_fund_info_tool(scheme_code: str) -> str:
    """Fetch metadata for an Indian mutual fund scheme: scheme name, fund house (AMC),
    scheme type, scheme category, latest NAV, and NAV date.
    scheme_code is the numeric MFApi scheme code (e.g. '119598')."""
    return route_to_vendor("get_fund_info", scheme_code)


@tool
def get_trailing_returns_tool(
    scheme_code: str,
    benchmark_code: str = "^NSEI",
) -> str:
    """Calculate trailing returns for an Indian mutual fund over 1M, 3M, 6M, 1Y, 3Y,
    and 5Y periods, compared against a benchmark index.
    scheme_code is the numeric MFApi scheme code.
    benchmark_code is a Yahoo Finance ticker (default '^NSEI' for Nifty 50)."""
    return route_to_vendor("get_trailing_returns", scheme_code, benchmark_code)


@tool
def search_fund_tool(query: str) -> str:
    """Search Indian mutual funds by partial name. Returns a list of matching fund
    scheme codes and names from MFApi. Use the scheme code in other fund tools."""
    return route_to_vendor("search_fund", query)


@tool
def get_fund_by_category_tool(category: str) -> str:
    """List all Indian mutual fund schemes in a given SEBI category from the AMFI
    NAV file. Example categories: 'Large Cap Fund', 'Mid Cap Fund', 'ELSS',
    'Liquid Fund', 'Gilt Fund'."""
    return route_to_vendor("get_category_funds", category)
