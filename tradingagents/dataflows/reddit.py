import requests


_HEADERS = {"User-Agent": "TradingAgents/1.0 (research tool)"}
_SUBREDDITS = ["wallstreetbets", "investing", "stocks"]


def get_reddit_sentiment(ticker: str, limit: int = 25) -> str:
    """Fetch recent Reddit posts mentioning a ticker (public JSON API, no auth)."""
    all_posts: list[dict] = []

    for subreddit in _SUBREDDITS:
        url = (
            f"https://www.reddit.com/r/{subreddit}/search.json"
            f"?q={ticker}&sort=new&limit={limit}&restrict_sr=1"
        )
        try:
            resp = requests.get(url, timeout=10, headers=_HEADERS)
            if resp.status_code != 200:
                continue
            children = resp.json().get("data", {}).get("children", [])
            for child in children:
                post = child.get("data", {})
                all_posts.append({
                    "subreddit": subreddit,
                    "title":     post.get("title", ""),
                    "score":     post.get("score", 0),
                    "comments":  post.get("num_comments", 0),
                    "url":       post.get("url", ""),
                })
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue

    if not all_posts:
        return f"<Reddit data unavailable for {ticker}>"

    # Sort by score descending
    all_posts.sort(key=lambda p: p["score"], reverse=True)

    lines = [f"Reddit posts mentioning {ticker} (top {min(limit, len(all_posts))} by score):"]
    for i, p in enumerate(all_posts[:limit], 1):
        lines.append(
            f"  {i:2d}. [r/{p['subreddit']}] ▲{p['score']} 💬{p['comments']} — {p['title']}"
        )
    return "\n".join(lines)
