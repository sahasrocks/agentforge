from .config import get_config
from .utils import AlphaVantageRateLimitError


# Maps each tool function name to its vendor config category
_TOOL_TO_CATEGORY: dict[str, str] = {
    "get_stock_data":           "core_stock_apis",
    "get_indicators":           "technical_indicators",
    "get_fundamentals":         "fundamental_data",
    "get_balance_sheet":        "fundamental_data",
    "get_cashflow":             "fundamental_data",
    "get_income_statement":     "fundamental_data",
    "get_news":                 "news_data",
    "get_global_news":          "news_data",
    "get_insider_transactions": "news_data",
    "get_reddit_sentiment":      "news_data",
    # Sentiment-only tools — each has a dedicated single vendor
    "get_stocktwits_sentiment":  "sentiment_data",
    "get_google_trends":         "sentiment_data",
    "get_fear_greed":            "sentiment_data",
    # Mutual fund tools route through fund_data_vendors
    "get_fund_nav_history":     "nav_data",
    "get_fund_info":            "fund_info",
    "get_trailing_returns":     "nav_data",
    "search_fund":              "nav_data",
    "get_category_funds":       "fund_info",
}

# All known stock/news/sentiment vendors in priority order
_STOCK_VENDORS = [
    "tavily", "rss_news", "newsapi", "finnhub",
    "yfinance", "alpha_vantage",
    "reddit", "stocktwits", "google_trends", "fear_greed",
]
# All known fund vendors
_FUND_VENDORS  = ["mfapi", "amfi"]


def _load_vendor_module(vendor: str):
    """Lazy-import the vendor module so unused SDKs are never loaded."""
    if vendor == "tavily":
        from . import tavily
        return tavily
    if vendor == "rss_news":
        from . import rss_news
        return rss_news
    if vendor == "newsapi":
        from . import newsapi
        return newsapi
    if vendor == "finnhub":
        from . import finnhub
        return finnhub
    if vendor == "yfinance":
        from . import y_finance
        return y_finance
    if vendor == "alpha_vantage":
        from . import alpha_vantage_stock
        return alpha_vantage_stock
    if vendor == "mfapi":
        from . import mfapi
        return mfapi
    if vendor == "amfi":
        from . import amfi
        return amfi
    if vendor == "reddit":
        from . import reddit
        return reddit
    if vendor == "stocktwits":
        from . import stocktwits
        return stocktwits
    if vendor == "google_trends":
        from . import google_trends
        return google_trends
    if vendor == "fear_greed":
        from . import fear_greed
        return fear_greed
    raise ValueError(f"Unknown vendor: '{vendor}'")


def route_to_vendor(method_name: str, *args, **kwargs):
    """Dispatch a tool call to the appropriate vendor with automatic fallback.

    Resolution order:
    1. tool_vendors[method_name]  — tool-level override (highest priority)
    2. data_vendors[category]     — category-level default
    3. fallback chain             — all other vendors tried in order
    """
    config = get_config()

    # Determine primary vendor — tool_vendors overrides take precedence
    all_vendors = _STOCK_VENDORS          # default; overridden below for fund tools
    primary     = config.get("tool_vendors", {}).get(method_name)
    if not primary:
        category = _TOOL_TO_CATEGORY.get(method_name, "")
        if category in ("nav_data", "fund_info"):
            primary     = config.get("fund_data_vendors", {}).get(category, "mfapi")
            all_vendors = _FUND_VENDORS
        else:
            primary = config.get("data_vendors", {}).get(category, "yfinance")
            # all_vendors stays as _STOCK_VENDORS

    fallback_chain = [primary] + [v for v in all_vendors if v != primary]

    last_exc: Exception | None = None
    for vendor in fallback_chain:
        try:
            module = _load_vendor_module(vendor)
            fn = getattr(module, method_name, None)
            if fn is None:
                continue  # this vendor doesn't implement the method
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            continue  # try next vendor in chain

    raise RuntimeError(
        f"All vendors failed for '{method_name}'. "
        f"Chain tried: {fallback_chain}. Last error: {last_exc}"
    )
