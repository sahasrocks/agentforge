from tradingagents.dataflows.config import get_config


def make_invest_debate_router():
    """Return a router function for the investment debate (bull ↔ bear)."""

    def router(state: dict) -> str:
        config      = get_config()
        max_rounds  = config.get("max_debate_rounds", 1)
        debate      = state.get("investment_debate_state", {})
        count       = debate.get("count", 0)

        # Each full round = bull speaks (1) + bear speaks (1) = 2 increments
        if count < max_rounds * 2:
            return "bear_researcher"
        return "research_manager"

    return router


def make_bear_router():
    """Bear always hands back to bull for the next round."""

    def router(state: dict) -> str:
        config     = get_config()
        max_rounds = config.get("max_debate_rounds", 1)
        debate     = state.get("investment_debate_state", {})
        count      = debate.get("count", 0)

        if count < max_rounds * 2:
            return "bull_researcher"
        return "research_manager"

    return router


def make_risk_debate_router():
    """Return a router function for the three-way risk debate."""

    def router(state: dict) -> str:
        config     = get_config()
        max_rounds = config.get("max_risk_discuss_rounds", 1)
        debate     = state.get("risk_debate_state", {})
        count      = debate.get("count", 0)
        speaker    = debate.get("latest_speaker", "")

        # Each full round = aggressive(1) + conservative(1) + neutral(1) = 3 increments
        if count >= max_rounds * 3:
            return "portfolio_manager"
        if speaker == "Aggressive":
            return "conservative_debator"
        if speaker == "Conservative":
            return "neutral_debator"
        # Neutral or first round → aggressive goes next
        return "aggressive_debator"

    return router
