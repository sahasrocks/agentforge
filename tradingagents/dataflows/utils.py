import re
from datetime import datetime, timedelta


class AlphaVantageRateLimitError(Exception):
    pass


def safe_ticker_component(ticker: str) -> str:
    """Strip characters unsafe for filenames. e.g. 'RELIANCE.NS' → 'RELIANCE_NS'"""
    return re.sub(r"[^\w]", "_", ticker)


def get_date_range(curr_date: str, look_back_days: int) -> tuple[str, str]:
    """Return (start_date, end_date) as 'YYYY-MM-DD' strings."""
    end = datetime.strptime(curr_date, "%Y-%m-%d")
    start = end - timedelta(days=look_back_days)
    return start.strftime("%Y-%m-%d"), curr_date


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_number(value) -> str:
    """Format large numbers with K/M/B suffixes."""
    try:
        v = float(value)
        if abs(v) >= 1e9:
            return f"{v/1e9:.2f}B"
        if abs(v) >= 1e6:
            return f"{v/1e6:.2f}M"
        if abs(v) >= 1e3:
            return f"{v/1e3:.2f}K"
        return f"{v:.2f}"
    except (TypeError, ValueError):
        return str(value)
