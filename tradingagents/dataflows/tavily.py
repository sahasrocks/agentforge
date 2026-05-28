import os
from datetime import datetime

_TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")

_GLOBAL_QUERIES = [
    "global stock market outlook today",
    "Federal Reserve interest rates inflation economy",
    "S&P 500 earnings GDP economic outlook",
    "geopolitical risk trade war commodities energy",
    "ECB Bank of England central bank policy",
]


def _client():
    from tavily import TavilyClient
    if not _TAVILY_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set")
    return TavilyClient(api_key=_TAVILY_KEY)


def _date_to_days(start_date: str, end_date: str) -> int:
    """Return lookback window in days (clamped to 1..90)."""
    try:
        delta = datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")
        return max(1, min(delta.days + 1, 90))
    except Exception:
        return 30


def _format_result(i: int, item: dict) -> list[str]:
    title   = item.get("title", "No title")
    url     = item.get("url", "")
    content = (item.get("content", "") or "")[:250].strip()
    lines   = [f"  {i}. {title}"]
    if content:
        lines.append(f"     {content}")
    if url:
        lines.append(f"     Source: {url}")
    return lines


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Fetch company-specific news via Tavily search."""
    try:
        cl   = _client()
        days = _date_to_days(start_date, end_date)

        # For numeric scheme codes (Indian mutual funds) use a generic finance query
        if ticker.isdigit():
            query = f"Indian mutual fund scheme {ticker} NAV performance news"
        else:
            query = f"{ticker} stock news earnings analysis latest"

        resp    = cl.search(query=query, search_depth="basic", max_results=10, days=days)
        results = resp.get("results", [])

        if not results:
            return f"No news found for {ticker} via Tavily ({start_date} to {end_date})."

        lines = [f"News for {ticker} ({start_date} to {end_date}):"]
        for i, item in enumerate(results, 1):
            lines.extend(_format_result(i, item))

        return "\n".join(lines)
    except Exception as exc:
        return f"Tavily error fetching news for {ticker}: {exc}"


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Fetch global macro/financial market news via Tavily."""
    try:
        cl    = _client()
        seen  = set()
        lines = [f"Global Market News (as of {curr_date}):"]
        count = 0

        for query in _GLOBAL_QUERIES:
            if count >= limit:
                break
            resp    = cl.search(query=query, search_depth="basic", max_results=5, days=look_back_days)
            results = resp.get("results", [])
            for item in results:
                if count >= limit:
                    break
                title = item.get("title", "No title")
                if title in seen:
                    continue
                seen.add(title)
                count += 1
                lines.extend(_format_result(count, item))

        if count == 0:
            return "No global market news found via Tavily."

        return "\n".join(lines)
    except Exception as exc:
        return f"Tavily error fetching global news: {exc}"
