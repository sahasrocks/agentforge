import os
import requests

_KEY  = os.environ.get("NEWSAPI_KEY", "")
_BASE = "https://newsapi.org/v2"


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Fetch company news from NewsAPI.org (requires NEWSAPI_KEY)."""
    if not _KEY:
        raise RuntimeError("NEWSAPI_KEY not set — skipping NewsAPI")
    try:
        params = {
            "q":        f'"{ticker}" stock',
            "from":     start_date,
            "to":       end_date,
            "language": "en",
            "sortBy":   "relevancy",
            "pageSize": 15,
            "apiKey":   _KEY,
        }
        resp = requests.get(f"{_BASE}/everything", params=params, timeout=12)
        data = resp.json()

        if data.get("status") != "ok":
            raise RuntimeError(f"NewsAPI: {data.get('message', 'error')}")

        articles = data.get("articles", [])
        if not articles:
            return f"No NewsAPI articles found for {ticker} ({start_date} to {end_date})."

        lines = [f"News for {ticker} ({start_date} to {end_date}) via NewsAPI:"]
        for i, art in enumerate(articles, 1):
            title  = art.get("title") or "No title"
            source = (art.get("source") or {}).get("name", "Unknown")
            date   = (art.get("publishedAt") or "")[:10]
            desc   = (art.get("description") or "")[:150]
            lines.append(f"  {i}. [{date}] [{source}] {title}")
            if desc:
                lines.append(f"     {desc}")
        return "\n".join(lines)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"NewsAPI fetch error: {exc}") from exc


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Fetch global business headlines from NewsAPI.org."""
    if not _KEY:
        raise RuntimeError("NEWSAPI_KEY not set — skipping NewsAPI")
    try:
        params = {
            "category": "business",
            "language": "en",
            "pageSize": min(limit, 20),
            "apiKey":   _KEY,
        }
        resp = requests.get(f"{_BASE}/top-headlines", params=params, timeout=12)
        data = resp.json()

        if data.get("status") != "ok":
            raise RuntimeError(f"NewsAPI: {data.get('message', 'error')}")

        articles = data.get("articles", [])
        if not articles:
            return "No global business headlines from NewsAPI."

        lines = [f"Global Business Headlines (NewsAPI, as of {curr_date}):"]
        for i, art in enumerate(articles, 1):
            title  = art.get("title") or "No title"
            source = (art.get("source") or {}).get("name", "Unknown")
            date   = (art.get("publishedAt") or "")[:10]
            lines.append(f"  {i}. [{date}] [{source}] {title}")
        return "\n".join(lines)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"NewsAPI fetch error: {exc}") from exc
