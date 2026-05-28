from datetime import datetime, timedelta

import requests
import yfinance as yf

from .utils import get_date_range

_BASE = "https://api.mfapi.in/mf"
_TIMEOUT = 15


def _parse_mfapi_date(date_str: str) -> datetime:
    """MFApi returns dates as 'DD-MM-YYYY'; convert to datetime."""
    return datetime.strptime(date_str, "%d-%m-%Y")


def _fetch_scheme(scheme_code: str) -> dict:
    resp = requests.get(f"{_BASE}/{scheme_code}", timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "SUCCESS":
        raise ValueError(f"MFApi returned non-success status for scheme {scheme_code}")
    return data


# ── Fund NAV History ───────────────────────────────────────────────────────────

def get_fund_nav_history(scheme_code: str, start_date: str, end_date: str) -> str:
    """Return NAV history for an Indian mutual fund scheme as CSV."""
    try:
        data = _fetch_scheme(scheme_code)
        nav_list = data.get("data", [])

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt   = datetime.strptime(end_date,   "%Y-%m-%d")

        filtered = [
            (entry["date"], entry["nav"])
            for entry in nav_list
            if start_dt <= _parse_mfapi_date(entry["date"]) <= end_dt
        ]

        if not filtered:
            return f"No NAV data for scheme {scheme_code} between {start_date} and {end_date}."

        lines = ["Date,NAV"] + [f"{d},{n}" for d, n in filtered]
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching NAV history for scheme {scheme_code}: {e}"


# ── Fund Info ──────────────────────────────────────────────────────────────────

def get_fund_info(scheme_code: str) -> str:
    """Return fund metadata: name, AMC, category, type."""
    try:
        data = _fetch_scheme(scheme_code)
        meta = data.get("meta", {})
        nav_list = data.get("data", [])

        latest_nav  = nav_list[0]["nav"]  if nav_list else "N/A"
        latest_date = nav_list[0]["date"] if nav_list else "N/A"

        fields = {
            "Scheme Code":     scheme_code,
            "Scheme Name":     meta.get("scheme_name", "N/A"),
            "Fund House":      meta.get("fund_house", "N/A"),
            "Scheme Type":     meta.get("scheme_type", "N/A"),
            "Scheme Category": meta.get("scheme_category", "N/A"),
            "Latest NAV":      latest_nav,
            "NAV Date":        latest_date,
        }
        lines = [f"{k}: {v}" for k, v in fields.items()]
        return "Mutual Fund Info:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching fund info for scheme {scheme_code}: {e}"


# ── Trailing Returns ───────────────────────────────────────────────────────────

def get_trailing_returns(scheme_code: str, benchmark_code: str = "^NSEI") -> str:
    """Calculate 1M/3M/6M/1Y/3Y/5Y trailing returns vs benchmark."""
    try:
        data     = _fetch_scheme(scheme_code)
        nav_list = data.get("data", [])
        meta     = data.get("meta", {})

        if not nav_list:
            return f"No NAV data available for scheme {scheme_code}."

        # Build date → NAV dict (MFApi returns newest first)
        nav_map: dict[datetime, float] = {}
        for entry in nav_list:
            dt  = _parse_mfapi_date(entry["date"])
            nav_map[dt] = float(entry["nav"])

        sorted_dates = sorted(nav_map.keys(), reverse=True)
        latest_date  = sorted_dates[0]
        latest_nav   = nav_map[latest_date]

        periods = {
            "1M":  30,
            "3M":  90,
            "6M":  180,
            "1Y":  365,
            "3Y":  365 * 3,
            "5Y":  365 * 5,
        }

        def closest_nav(target_dt: datetime) -> float | None:
            for d in sorted(nav_map.keys(), reverse=True):
                if d <= target_dt:
                    return nav_map[d]
            return None

        # Benchmark via yfinance
        benchmark_returns: dict[str, str] = {}
        try:
            bm_end   = latest_date.strftime("%Y-%m-%d")
            bm_start = (latest_date - timedelta(days=365 * 5 + 30)).strftime("%Y-%m-%d")
            bm_df    = yf.download(benchmark_code, start=bm_start, end=bm_end,
                                   auto_adjust=True, progress=False)
        except Exception:
            bm_df = None

        lines = [
            f"Trailing Returns: {meta.get('scheme_name', scheme_code)}",
            f"Latest NAV: {latest_nav:.4f} ({latest_date.strftime('%d-%m-%Y')})",
            "",
            f"{'Period':<6} {'Fund Return':>12} {'Benchmark':>12}",
            "-" * 34,
        ]

        for label, days in periods.items():
            past_dt   = latest_date - timedelta(days=days)
            past_nav  = closest_nav(past_dt)
            if past_nav is None:
                fund_ret = "N/A"
            else:
                fund_ret = f"{((latest_nav / past_nav) - 1) * 100:+.2f}%"

            bm_ret = "N/A"
            if bm_df is not None and not bm_df.empty:
                try:
                    import pandas as pd
                    if isinstance(bm_df.columns, pd.MultiIndex):
                        bm_df.columns = bm_df.columns.get_level_values(0)
                    close = bm_df["Close"]
                    past_bm  = close[close.index <= pd.Timestamp(past_dt)].iloc[-1]
                    now_bm   = close.iloc[-1]
                    bm_ret   = f"{((now_bm / past_bm) - 1) * 100:+.2f}%"
                except Exception:
                    pass

            lines.append(f"{label:<6} {fund_ret:>12} {bm_ret:>12}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error calculating trailing returns for scheme {scheme_code}: {e}"


# ── Fund Search ────────────────────────────────────────────────────────────────

def search_fund(query: str) -> str:
    """Search Indian mutual funds by name. Returns scheme codes and names."""
    try:
        resp = requests.get(f"{_BASE}/search?q={query}", timeout=_TIMEOUT)
        resp.raise_for_status()
        results = resp.json()

        if not results:
            return f"No funds found matching '{query}'."

        lines = [f"Funds matching '{query}':"]
        for i, fund in enumerate(results[:20], 1):
            code = fund.get("schemeCode", "N/A")
            name = fund.get("schemeName", "N/A")
            lines.append(f"  {i:2d}. [{code}] {name}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching funds for '{query}': {e}"
