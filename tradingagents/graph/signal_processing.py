import os
import re
from datetime import datetime

from tradingagents.agents.utils.rating import parse_rating

_REPORTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "reports")
)

_NA_SENTINEL = "N/A — asset is not a mutual fund."


def extract_final_signal(result: dict) -> dict:
    """Extract the clean output signal from the raw graph result dict."""
    final_decision  = result.get("final_trade_decision", "")
    invest_debate   = result.get("investment_debate_state", {})
    return {
        "ticker":          result.get("company_of_interest", ""),
        "asset_type":      result.get("asset_type", "stock"),
        "trade_date":      result.get("trade_date", ""),
        "rating":          parse_rating(final_decision),
        "final_decision":  final_decision,
        "investment_plan": result.get("investment_plan", ""),
        "trader_proposal": result.get("trader_investment_plan", ""),
        "bull_research":   invest_debate.get("bull_history", ""),
        "bear_research":   invest_debate.get("bear_history", ""),
        "market_report":        result.get("market_report", ""),
        "fundamentals_report":  result.get("fundamentals_report", ""),
        "news_report":          result.get("news_report", ""),
        "sentiment_report":     result.get("sentiment_report", ""),
        "holdings_report":      result.get("holdings_report", ""),
        "category_report":      result.get("category_report", ""),
    }


def _section(title: str, content: str) -> str:
    if not content or content == _NA_SENTINEL:
        return ""
    return f"## {title}\n\n{content.strip()}\n\n"


def save_report(signal: dict, output_dir: str | None = None) -> str:
    """Write the full analysis report as a markdown file.

    Returns the absolute path of the saved file.
    """
    out_dir = output_dir or _REPORTS_DIR
    os.makedirs(out_dir, exist_ok=True)

    ticker     = signal.get("ticker", "unknown")
    trade_date = signal.get("trade_date", datetime.utcnow().strftime("%Y-%m-%d"))
    rating     = signal.get("rating", "Hold")
    asset_type = signal.get("asset_type", "stock")

    # Safe filename: replace characters that are invalid on Windows/Linux
    safe_ticker = re.sub(r'[\\/*?:"<>|]', "_", ticker)
    filename    = f"{safe_ticker}_{trade_date}.md"
    filepath    = os.path.join(out_dir, filename)

    lines = [
        f"# TradingAgents Report — {ticker}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Ticker | {ticker} |",
        f"| Asset Type | {asset_type} |",
        f"| Analysis Date | {trade_date} |",
        f"| Rating | **{rating}** |",
        f"| Generated | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} |",
        "",
        "---",
        "",
    ]

    lines.append(_section("Final Portfolio Decision", signal.get("final_decision", "")))
    lines.append(_section("Investment Plan",          signal.get("investment_plan", "")))
    lines.append(_section("Trader Proposal",          signal.get("trader_proposal", "")))
    lines.append(_section("Bull Research",            signal.get("bull_research", "")))
    lines.append(_section("Bear Research",            signal.get("bear_research", "")))
    lines.append(_section("Market / Technical Analysis", signal.get("market_report", "")))
    lines.append(_section("Fundamentals Analysis",    signal.get("fundamentals_report", "")))
    lines.append(_section("News Analysis",            signal.get("news_report", "")))
    lines.append(_section("Sentiment Analysis",       signal.get("sentiment_report", "")))
    lines.append(_section("Fund Holdings Analysis",   signal.get("holdings_report", "")))
    lines.append(_section("Fund Category Analysis",   signal.get("category_report", "")))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath
