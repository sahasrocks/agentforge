import requests


def get_stocktwits_sentiment(ticker: str, limit: int = 30) -> str:
    """Fetch recent StockTwits messages for a ticker (public API, no auth)."""
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return f"<StockTwits data unavailable for {ticker} (HTTP {resp.status_code})>"

        data     = resp.json()
        messages = data.get("messages", [])
        if not messages:
            return f"No StockTwits messages found for {ticker}."

        lines = [f"StockTwits sentiment for ${ticker} (latest {min(limit, len(messages))} messages):"]
        for msg in messages[:limit]:
            body      = msg.get("body", "").replace("\n", " ").strip()
            sentiment = msg.get("entities", {}).get("sentiment", {})
            label     = sentiment.get("basic", "Neutral") if sentiment else "Neutral"
            username  = msg.get("user", {}).get("username", "anon")
            lines.append(f"  [{label:9s}] @{username}: {body}")

        return "\n".join(lines)
    except requests.exceptions.Timeout:
        return f"<StockTwits request timed out for {ticker}>"
    except Exception as e:
        return f"<StockTwits error for {ticker}: {e}>"
