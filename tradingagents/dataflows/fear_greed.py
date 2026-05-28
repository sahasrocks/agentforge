import requests
from datetime import datetime

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TradingAgents/1.0)"}


def _cnn_fear_greed() -> list[str]:
    resp = requests.get(
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        headers=_HEADERS,
        timeout=12,
    )
    resp.raise_for_status()
    data = resp.json()

    fg     = data.get("fear_and_greed", {})
    score  = fg.get("score", "N/A")
    rating = (fg.get("rating") or "N/A").upper()

    score_str = f"{score:.1f}" if isinstance(score, (int, float)) else str(score)
    lines = [
        "CNN Money Fear & Greed Index (Stock Market):",
        f"  Current: {score_str}/100 — {rating}",
    ]

    historical = data.get("fear_and_greed_historical", {}).get("data", [])
    if historical:
        lines.append("  Recent history:")
        for entry in historical[-7:]:
            ts_ms  = entry.get("x", 0)
            val    = entry.get("y", "N/A")
            label  = entry.get("rating", "")
            date_s = datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d") if ts_ms else ""
            val_s  = f"{val:.1f}" if isinstance(val, (int, float)) else str(val)
            lines.append(f"    {date_s}: {val_s}/100 ({label})")
    return lines


def _alt_fear_greed() -> list[str]:
    resp = requests.get(
        "https://api.alternative.me/fng/?limit=7&format=json",
        headers=_HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    entries = resp.json().get("data", [])

    lines = ["Alternative.me Fear & Greed (Crypto — corroborating signal):"]
    for entry in entries:
        val    = entry.get("value", "N/A")
        label  = entry.get("value_classification", "")
        ts     = entry.get("timestamp", "")
        date_s = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d") if ts else ""
        lines.append(f"  {date_s}: {val}/100 — {label}")
    return lines


def get_fear_greed(curr_date: str) -> str:
    """Fetch CNN Money Fear & Greed Index (stocks) and Alternative.me (crypto)."""
    parts = []

    try:
        parts.extend(_cnn_fear_greed())
    except Exception as exc:
        parts.append(f"CNN Fear & Greed unavailable: {exc}")

    parts.append("")  # blank separator

    try:
        parts.extend(_alt_fear_greed())
    except Exception as exc:
        parts.append(f"Alternative.me unavailable: {exc}")

    result = "\n".join(parts).strip()
    if not result:
        raise RuntimeError("Fear & Greed data unavailable from all sources")
    return result
