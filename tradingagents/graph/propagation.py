def initialise_state(
    ticker: str,
    trade_date: str,
    config: dict,
    past_context: str = "",
) -> dict:
    """Build the initial AgentState dict for a new graph run."""
    return {
        # Identity
        "company_of_interest": ticker,
        "asset_type":          config.get("asset_type", "stock"),
        "trade_date":          trade_date,
        "sender":              "system",
        # Analyst outputs — all start empty
        "market_report":        "",
        "fundamentals_report":  "",
        "news_report":          "",
        "sentiment_report":     "",
        "holdings_report":      "",
        "category_report":      "",
        # Fund-specific
        "fund_benchmark": config.get("fund_category_benchmarks", {}).get("default", "^NSEI"),
        # Investment debate
        "investment_debate_state": {
            "bull_history":     "",
            "bear_history":     "",
            "history":          "",
            "current_response": "",
            "judge_decision":   "",
            "count":            0,
        },
        "investment_plan":        "",
        # Trading
        "trader_investment_plan": "",
        # Risk debate
        "risk_debate_state": {
            "aggressive_history":           "",
            "conservative_history":         "",
            "neutral_history":              "",
            "history":                      "",
            "latest_speaker":               "",
            "current_aggressive_response":  "",
            "current_conservative_response": "",
            "current_neutral_response":     "",
            "judge_decision":               "",
            "count":                        0,
        },
        "final_trade_decision": "",
        # Memory
        "past_context": past_context,
        "messages":     [],
    }
