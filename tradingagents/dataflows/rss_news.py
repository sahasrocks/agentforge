import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TradingAgents/1.0)"}

_GLOBAL_RSS_URLS = [
    "https://news.google.com/rss/search?q=stock+market+today&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=federal+reserve+interest+rates+economy&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=S%26P+500+earnings+GDP+outlook&hl=en-US&gl=US&ceid=US:en",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.reuters.com/reuters/businessNews",
]


def _fetch_rss(url: str) -> list[dict]:
    try:
        resp = requests.get(url, timeout=10, headers=_HEADERS)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link")  or "").strip()
        pub   = (item.findtext("pubDate") or "").strip()
        desc  = (item.findtext("description") or "").strip()

        date_str = ""
        if pub:
            try:
                date_str = parsedate_to_datetime(pub).strftime("%Y-%m-%d")
            except Exception:
                date_str = pub[:10]

        # Strip HTML tags from description
        desc = ET.tostring(ET.fromstring(f"<x>{desc}</x>"), method="text", encoding="unicode") if "<" in desc else desc
        items.append({"title": title, "link": link, "date": date_str, "summary": desc[:200]})

    return items


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Fetch company news via Yahoo Finance and Google News RSS feeds."""
    sources = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
        f"https://news.google.com/rss/search?q={ticker}+stock+news&hl=en-US&gl=US&ceid=US:en",
    ]

    seen, all_items = set(), []
    for url in sources:
        for item in _fetch_rss(url):
            if item["title"] and item["title"] not in seen:
                seen.add(item["title"])
                all_items.append(item)

    if not all_items:
        return f"No RSS news found for {ticker}."

    lines = [f"News for {ticker} ({start_date} to {end_date}) via RSS:"]
    for i, item in enumerate(all_items[:15], 1):
        lines.append(f"  {i}. [{item['date']}] {item['title']}")
        if item["summary"]:
            lines.append(f"     {item['summary'][:150]}")
    return "\n".join(lines)


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Fetch global market/macro news from multiple RSS sources."""
    seen, all_items = set(), []
    for url in _GLOBAL_RSS_URLS:
        for item in _fetch_rss(url):
            if item["title"] and item["title"] not in seen:
                seen.add(item["title"])
                all_items.append(item)
        if len(all_items) >= limit * 2:
            break

    if not all_items:
        return "No global news found via RSS feeds."

    lines = [f"Global Market News (RSS, as of {curr_date}):"]
    for i, item in enumerate(all_items[:limit], 1):
        lines.append(f"  {i}. [{item['date']}] {item['title']}")
        if item["summary"]:
            lines.append(f"     {item['summary'][:150]}")
    return "\n".join(lines)
