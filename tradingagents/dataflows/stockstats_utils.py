import yfinance as yf
import pandas as pd
from stockstats import wrap

from .utils import get_date_range

SUPPORTED_INDICATORS = (
    "close_50_sma", "close_200_sma", "close_10_ema",
    "macd", "macds", "macdh",
    "rsi",
    "boll", "boll_ub", "boll_lb",
    "atr", "vwma", "mfi",
)


def get_indicators(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int = 30,
) -> str:
    """Calculate one or more technical indicators for a symbol.

    ``indicator`` can be a single name or comma-separated list,
    e.g. ``"rsi,macd,close_50_sma"``.
    """
    start_date, _ = get_date_range(curr_date, look_back_days + 250)

    try:
        df = yf.download(symbol, start=start_date, end=curr_date, auto_adjust=True, progress=False)
        if df.empty:
            return f"No price data for {symbol} to compute indicators."

        # Flatten MultiIndex columns produced by newer yfinance versions
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = df.columns.str.lower()
        df = df.rename(columns={"adj close": "close"})

        stock = wrap(df.copy())
    except Exception as e:
        return f"Error loading price data for {symbol}: {e}"

    requested = [ind.strip() for ind in indicator.split(",") if ind.strip()]
    results: list[str] = []

    for ind in requested:
        try:
            series = stock[ind].dropna().tail(look_back_days)
            if series.empty:
                results.append(f"{ind}: no data")
                continue
            formatted = series.round(4).to_string()
            results.append(f"--- {ind.upper()} ---\n{formatted}")
        except Exception as e:
            results.append(f"{ind}: unavailable ({e})")

    if not results:
        return f"No indicators computed for {symbol}."

    header = f"Technical Indicators for {symbol} (last {look_back_days} days, as of {curr_date})"
    return header + "\n\n" + "\n\n".join(results)
