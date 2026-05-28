from langgraph.graph import StateGraph, START, END

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.dataflows.config import set_config
from tradingagents.llm_clients.factory import create_llm_client

from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.analysts.sentiment_analyst import create_sentiment_analyst
from tradingagents.agents.analysts.holdings_analyst import create_holdings_analyst
from tradingagents.agents.analysts.category_analyst import create_category_analyst

from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
from tradingagents.agents.researchers.bear_researcher import create_bear_researcher
from tradingagents.agents.managers.research_manager import create_research_manager

from tradingagents.agents.trader.trader import create_trader

from tradingagents.agents.risk_mgmt.aggressive_debator import create_aggressive_debator
from tradingagents.agents.risk_mgmt.conservative_debator import create_conservative_debator
from tradingagents.agents.risk_mgmt.neutral_debator import create_neutral_debator
from tradingagents.agents.managers.portfolio_manager import create_portfolio_manager

from tradingagents.graph.analyst_execution import get_analyst_node_names
from tradingagents.graph.conditional_logic import (
    make_invest_debate_router,
    make_bear_router,
    make_risk_debate_router,
)
from tradingagents.graph.checkpointer import get_checkpointer


def build_graph(config: dict):
    """Assemble and compile the full TradingAgents LangGraph."""

    # Make config available to route_to_vendor inside tool calls
    set_config(config)

    provider  = config.get("llm_provider", "openai")
    deep_llm  = create_llm_client(provider, config.get("deep_think_llm",  "gpt-4o")).get_llm()
    quick_llm = create_llm_client(provider, config.get("quick_think_llm", "gpt-4o-mini")).get_llm()

    # ── Instantiate all agent nodes ────────────────────────────────────────────
    market_analyst_node      = create_market_analyst(quick_llm, config)
    fundamentals_analyst_node = create_fundamentals_analyst(deep_llm, config)
    news_analyst_node        = create_news_analyst(quick_llm, config)
    sentiment_analyst_node   = create_sentiment_analyst(quick_llm, config)
    holdings_analyst_node    = create_holdings_analyst(deep_llm, config)
    category_analyst_node    = create_category_analyst(quick_llm, config)

    bull_researcher_node  = create_bull_researcher(deep_llm, config)
    bear_researcher_node  = create_bear_researcher(deep_llm, config)
    research_manager_node = create_research_manager(deep_llm, config)

    trader_node = create_trader(deep_llm, config)

    aggressive_node  = create_aggressive_debator(quick_llm, config)
    conservative_node = create_conservative_debator(quick_llm, config)
    neutral_node      = create_neutral_debator(quick_llm, config)
    portfolio_manager_node = create_portfolio_manager(deep_llm, config)

    # ── Build the graph ────────────────────────────────────────────────────────
    graph = StateGraph(AgentState)

    graph.add_node("market_analyst",       market_analyst_node)
    graph.add_node("fundamentals_analyst", fundamentals_analyst_node)
    graph.add_node("news_analyst",         news_analyst_node)
    graph.add_node("sentiment_analyst",    sentiment_analyst_node)
    graph.add_node("holdings_analyst",     holdings_analyst_node)
    graph.add_node("category_analyst",     category_analyst_node)

    graph.add_node("bull_researcher",  bull_researcher_node)
    graph.add_node("bear_researcher",  bear_researcher_node)
    graph.add_node("research_manager", research_manager_node)

    graph.add_node("trader", trader_node)

    graph.add_node("aggressive_debator",  aggressive_node)
    graph.add_node("conservative_debator", conservative_node)
    graph.add_node("neutral_debator",     neutral_node)
    graph.add_node("portfolio_manager",   portfolio_manager_node)

    # ── Edges: START → analysts (run in parallel) ──────────────────────────────
    asset_type     = config.get("asset_type", "stock")
    analyst_names  = get_analyst_node_names(asset_type)

    for analyst in analyst_names:
        graph.add_edge(START, analyst)

    # ── Edges: analysts → bull_researcher (fan-in; waits for all analysts) ─────
    for analyst in analyst_names:
        graph.add_edge(analyst, "bull_researcher")

    # ── Investment debate loop ─────────────────────────────────────────────────
    invest_router = make_invest_debate_router()
    bear_router   = make_bear_router()

    graph.add_conditional_edges(
        "bull_researcher",
        invest_router,
        {"bear_researcher": "bear_researcher", "research_manager": "research_manager"},
    )
    graph.add_conditional_edges(
        "bear_researcher",
        bear_router,
        {"bull_researcher": "bull_researcher", "research_manager": "research_manager"},
    )

    # ── Research manager → trader ──────────────────────────────────────────────
    graph.add_edge("research_manager", "trader")

    # ── Risk debate loop ───────────────────────────────────────────────────────
    risk_router = make_risk_debate_router()

    graph.add_edge("trader", "aggressive_debator")

    graph.add_conditional_edges(
        "aggressive_debator",
        risk_router,
        {
            "conservative_debator": "conservative_debator",
            "portfolio_manager":    "portfolio_manager",
        },
    )
    graph.add_conditional_edges(
        "conservative_debator",
        risk_router,
        {
            "neutral_debator":   "neutral_debator",
            "portfolio_manager": "portfolio_manager",
        },
    )
    graph.add_conditional_edges(
        "neutral_debator",
        risk_router,
        {
            "aggressive_debator": "aggressive_debator",
            "portfolio_manager":  "portfolio_manager",
        },
    )

    # ── Portfolio manager → END ────────────────────────────────────────────────
    graph.add_edge("portfolio_manager", END)

    # ── Compile ────────────────────────────────────────────────────────────────
    checkpointer = get_checkpointer(config)
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()
