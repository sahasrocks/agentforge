import os
import requests

from .utils import AlphaVantageRateLimitError

_AV_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
_BASE   = "https://www.alphavantage.co/query"
_RATE_LIMIT_MSG = "Thank you for using Alpha Vantage"


def _check_rate_limit(data: dict) -> None:
    note = data.get("Note", "") or data.get("Information", "")
    if _RATE_LIMIT_MSG in note:
        raise AlphaVantageRateLimitError("Alpha Vantage rate limit reached")


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Fetch company news via Alpha Vantage News & Sentiment API."""
    try:
        # AV expects dates as YYYYMMDDTHHMM
        time_from = start_date.replace("-", "") + "T0000"
        time_to   = end_date.replace("-", "")   + "T2359"
        params = {
            "function":  "NEWS_SENTIMENT",
            "tickers":   ticker,
            "time_from": time_from,
            "time_to":   time_to,
            "limit":     20,
            "apikey":    _AV_KEY,
        }
        resp = requests.get(_BASE, params=params, timeout=15)
        data = resp.json()
        _check_rate_limit(data)

        feed = data.get("feed", [])
        if not feed:
            return f"No Alpha Vantage news for {ticker} in range {start_date}–{end_date}."

        lines = [f"News for {ticker} (Alpha Vantage, {start_date} to {end_date}):"]
        for i, item in enumerate(feed, 1):
            title     = item.get("title", "No title")
            source    = item.get("source", "Unknown")
            published = item.get("time_published", "")[:8]  # YYYYMMDD
            sentiment = item.get("overall_sentiment_label", "Neutral")
            lines.append(f"  {i:2d}. [{published}] [{sentiment}] {title} — {source}")

        return "\n".join(lines)
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching news for {ticker}: {e}"


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Fetch global market news via Alpha Vantage (broad topics)."""
    try:
        time_from = curr_date.replace("-", "")
        params = {
            "function":  "NEWS_SENTIMENT",
            "topics":    "economy_macro,financial_markets",
            "time_from": f"{time_from}T0000",
            "limit":     limit,
            "apikey":    _AV_KEY,
        }
        resp = requests.get(_BASE, params=params, timeout=15)
        data = resp.json()
        _check_rate_limit(data)

        feed = data.get("feed", [])
        if not feed:
            return "No global news available from Alpha Vantage."

        lines = [f"Global Market News (Alpha Vantage, as of {curr_date}):"]
        for i, item in enumerate(feed, 1):
            title     = item.get("title", "No title")
            source    = item.get("source", "Unknown")
            published = item.get("time_published", "")[:8]
            sentiment = item.get("overall_sentiment_label", "Neutral")
            lines.append(f"  {i:2d}. [{published}] [{sentiment}] {title} — {source}")

        return "\n".join(lines)
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching global news: {e}"
