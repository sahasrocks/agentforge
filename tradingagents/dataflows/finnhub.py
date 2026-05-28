import os
import requests
from datetime import datetime

_KEY  = os.environ.get("FINNHUB_KEY", "")
_BASE = "https://finnhub.io/api/v1"


def _symbol(ticker: str) -> str:
    """Strip exchange suffix for Finnhub (e.g. RELIANCE.NS → RELIANCE)."""
    return ticker.split(".")[0] if "." in ticker else ticker


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Fetch company news from Finnhub (requires FINNHUB_KEY)."""
    if not _KEY:
        raise RuntimeError("FINNHUB_KEY not set — skipping Finnhub")
    try:
        params = {
            "symbol": _symbol(ticker),
            "from":   start_date,
            "to":     end_date,
            "token":  _KEY,
        }
        resp     = requests.get(f"{_BASE}/company-news", params=params, timeout=12)
        articles = resp.json()

        if not isinstance(articles, list):
            raise RuntimeError(f"Finnhub returned: {articles}")
        if not articles:
            return f"No Finnhub news for {ticker} ({start_date} to {end_date})."

        lines = [f"News for {ticker} ({start_date} to {end_date}) via Finnhub:"]
        for i, art in enumerate(articles[:15], 1):
            title    = art.get("headline") or "No title"
            source   = art.get("source", "Unknown")
            ts       = art.get("datetime", 0)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "N/A"
            summary  = (art.get("summary") or "")[:150]
            lines.append(f"  {i}. [{date_str}] [{source}] {title}")
            if summary:
                lines.append(f"     {summary}")
        return "\n".join(lines)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Finnhub fetch error: {exc}") from exc


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Fetch general market news from Finnhub."""
    if not _KEY:
        raise RuntimeError("FINNHUB_KEY not set — skipping Finnhub")
    try:
        params   = {"category": "general", "token": _KEY}
        resp     = requests.get(f"{_BASE}/news", params=params, timeout=12)
        articles = resp.json()

        if not isinstance(articles, list):
            raise RuntimeError(f"Finnhub returned: {articles}")
        if not articles:
            return "No global news from Finnhub."

        lines = [f"Global Market News (Finnhub, as of {curr_date}):"]
        for i, art in enumerate(articles[:limit], 1):
            title    = art.get("headline") or "No title"
            source   = art.get("source", "Unknown")
            ts       = art.get("datetime", 0)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "N/A"
            lines.append(f"  {i}. [{date_str}] [{source}] {title}")
        return "\n".join(lines)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Finnhub fetch error: {exc}") from exc
