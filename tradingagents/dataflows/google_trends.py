def get_google_trends(ticker: str, look_back_days: int = 30) -> str:
    """Return Google Search interest trend for a ticker via pytrends."""
    try:
        from pytrends.request import TrendReq
    except ImportError:
        raise RuntimeError("pytrends not installed — run: pip install pytrends")

    # Use bare symbol (strip exchange suffix) for better Trends results
    kw = ticker.split(".")[0] if "." in ticker else ticker
    # Numeric scheme codes (Indian MFs) have no useful Trends data
    if kw.isdigit():
        return f"Google Trends: no search-interest data for scheme code {kw}."

    try:
        timeframe = f"today {min(look_back_days, 89)}-d" if look_back_days <= 89 else "today 3-m"
        pt = TrendReq(hl="en-US", tz=330, timeout=(10, 25))
        pt.build_payload([kw], cat=0, timeframe=timeframe, geo="", gprop="")

        df = pt.interest_over_time()
        if df.empty or kw not in df.columns:
            return f"Google Trends: no data returned for {kw}."

        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])

        series  = df[kw]
        avg_all = series.mean()
        avg_rec = series.tail(7).mean()
        peak    = series.max()
        trough  = series.min()

        if avg_rec > avg_all * 1.15:
            trend = "Rising (above average)"
        elif avg_rec < avg_all * 0.85:
            trend = "Falling (below average)"
        else:
            trend = "Stable"

        lines = [
            f"Google Trends — {kw} (last {look_back_days} days):",
            f"  Trend direction : {trend}",
            f"  Period average  : {avg_all:.1f}/100",
            f"  Recent avg (7d) : {avg_rec:.1f}/100",
            f"  Peak / Trough   : {peak}/100 / {trough}/100",
            "  Weekly data:",
        ]
        weekly = series.resample("W").mean()
        for date, val in weekly.tail(8).items():
            lines.append(f"    {date.strftime('%Y-%m-%d')}: {int(val)}/100")

        return "\n".join(lines)
    except Exception as exc:
        raise RuntimeError(f"Google Trends error for {ticker}: {exc}") from exc
