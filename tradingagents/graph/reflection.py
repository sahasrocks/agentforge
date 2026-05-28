import json
import os
from datetime import datetime, timedelta

_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory_store.json")
_STORE_PATH = os.path.normpath(_STORE_PATH)

# In-memory cache; also persisted to JSON on disk
_memory: dict[str, list[dict]] = {}


def _load_from_disk() -> None:
    global _memory
    if os.path.exists(_STORE_PATH):
        try:
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                _memory = json.load(f)
        except Exception:
            _memory = {}


def _save_to_disk() -> None:
    try:
        with open(_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(_memory, f, indent=2)
    except Exception:
        pass


def reflect_and_store(ticker: str, trade_date: str, signal: dict, config: dict) -> None:
    """Persist a completed run's signal to the memory store."""
    _load_from_disk()
    entry = {
        "trade_date":     trade_date,
        "rating":         signal.get("rating", "Hold"),
        "final_decision": signal.get("final_decision", ""),
        "stored_at":      datetime.utcnow().isoformat(),
    }
    _memory.setdefault(ticker, []).append(entry)
    _save_to_disk()


def load_past_context(ticker: str, config: dict) -> str:
    """Return a formatted string of prior decisions for the same ticker within the lookback window."""
    _load_from_disk()
    entries = _memory.get(ticker, [])
    if not entries:
        return ""

    asset_type   = config.get("asset_type", "stock")
    window_days  = 30 if asset_type == "mutual_fund" else 5
    cutoff       = datetime.utcnow() - timedelta(days=window_days)

    recent = [
        e for e in entries
        if datetime.fromisoformat(e["stored_at"]) >= cutoff
    ]
    if not recent:
        return ""

    lines = [f"Prior decisions for {ticker} (last {window_days} days):"]
    for e in recent[-5:]:  # cap at 5 most recent
        lines.append(f"  [{e['trade_date']}] Rating: {e['rating']}")
        if e.get("final_decision"):
            # Include just the first 200 chars to avoid bloating context
            snippet = e["final_decision"][:200].replace("\n", " ")
            lines.append(f"    Summary: {snippet}...")
    return "\n".join(lines)
