def get_analyst_node_names(asset_type: str) -> list[str]:
    """Return the ordered list of analyst node names to run for a given asset type.

    For stocks: technical + fundamentals + news + sentiment.
    For mutual funds: NAV/performance + category/peers + news (no technicals/fundamentals).
    """
    if asset_type == "mutual_fund":
        return ["holdings_analyst", "category_analyst", "news_analyst"]
    return ["market_analyst", "fundamentals_analyst", "news_analyst", "sentiment_analyst"]
