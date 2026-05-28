from tradingagents.default_config import get_config
from tradingagents.graph.setup import build_graph
from tradingagents.graph.propagation import initialise_state
from tradingagents.graph.signal_processing import extract_final_signal, save_report
from tradingagents.graph.reflection import load_past_context, reflect_and_store


def run(
    ticker: str,
    trade_date: str,
    config: dict | None = None,
) -> dict:
    """Run the full TradingAgents pipeline for a single ticker and date.

    Returns a signal dict with keys:
        ticker, asset_type, trade_date, rating, final_decision,
        investment_plan, trader_proposal, and all analyst reports.
    """
    cfg = get_config(config)

    past_context  = load_past_context(ticker, cfg)
    compiled      = build_graph(cfg)
    initial_state = initialise_state(ticker, trade_date, cfg, past_context)

    result = compiled.invoke(initial_state)

    signal = extract_final_signal(result)
    reflect_and_store(ticker, trade_date, signal, cfg)
    save_report(signal)

    return signal
