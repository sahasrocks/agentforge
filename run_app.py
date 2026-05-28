"""Interactive TUI for TradingAgents — run with: python run_app.py"""

from datetime import date

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from tradingagents.llm_clients.model_catalog import get_all_providers, get_models_for_provider
from tradingagents.graph.trading_graph import run as graph_run
from tradingagents.graph.signal_processing import save_report

console = Console()

_RATING_COLOURS = {
    "Buy":         "bold green",
    "Overweight":  "green",
    "Hold":        "yellow",
    "Underweight": "red",
    "Sell":        "bold red",
}


def _ask_provider() -> str:
    return questionary.select(
        "LLM Provider:",
        choices=get_all_providers(),
    ).ask()


def _ask_model(provider: str) -> tuple[str, str]:
    """Return (deep_model, quick_model)."""
    models = get_models_for_provider(provider)

    if not models:
        # Open catalog (Ollama, OpenRouter) — user types manually
        deep  = questionary.text(f"Deep-think model name for {provider}:").ask().strip()
        quick = questionary.text(f"Quick-think model name for {provider} (Enter to reuse deep):").ask().strip()
        return deep, quick or deep

    deep = questionary.select("Deep-think model (complex reasoning):", choices=models).ask()
    quick_choices = models + ["(same as deep)"]
    quick_raw = questionary.select("Quick-think model (data gathering):", choices=quick_choices).ask()
    quick = deep if quick_raw == "(same as deep)" else quick_raw
    return deep, quick


def _ask_asset() -> str:
    return questionary.select(
        "Asset type:",
        choices=["stock", "mutual_fund"],
    ).ask()


def _ask_ticker(asset_type: str) -> str:
    if asset_type == "mutual_fund":
        console.print(
            "[dim]Tip: use MFApi scheme code (e.g. 119598). "
            "Not sure? Search at mfapi.in/mf/search?q=<name>[/dim]"
        )
        return questionary.text("MFApi Scheme Code:").ask().strip()

    console.print("[dim]Examples: RELIANCE.NS  TCS.NS  AAPL  TSLA[/dim]")
    return questionary.text("Ticker symbol:").ask().strip().upper()


def _ask_date() -> str:
    today = date.today().isoformat()
    raw = questionary.text(f"Analysis date (YYYY-MM-DD) [{today}]:").ask().strip()
    return raw if raw else today


def _ask_rounds() -> tuple[int, int]:
    invest_rounds = int(
        questionary.select(
            "Investment debate rounds (bull vs bear):",
            choices=["1", "2", "3"],
        ).ask()
    )
    risk_rounds = int(
        questionary.select(
            "Risk debate rounds (aggressive / conservative / neutral):",
            choices=["1", "2", "3"],
        ).ask()
    )
    return invest_rounds, risk_rounds


def _print_report_section(title: str, content: str) -> None:
    if not content or content.startswith("N/A"):
        return
    console.print(Rule(f"[bold]{title}[/bold]", style="dim"))
    console.print(content.strip())
    console.print()


def _display_results(signal: dict) -> None:
    console.print()
    rating  = signal.get("rating", "Hold")
    colour  = _RATING_COLOURS.get(rating, "white")
    ticker  = signal.get("ticker", "")
    tdate   = signal.get("trade_date", "")

    header = Text()
    header.append(f"{ticker}  ", style="bold white")
    header.append(f"[{tdate}]  ", style="dim")
    header.append(f"Rating: {rating}", style=colour)

    console.print(Panel(header, title="[bold]TradingAgents Result[/bold]", border_style=colour))
    console.print()

    final = signal.get("final_decision", "")
    if final:
        console.print(Panel(final.strip(), title="Final Portfolio Decision", border_style="blue"))
        console.print()

    _print_report_section("Investment Plan", signal.get("investment_plan", ""))
    _print_report_section("Trader Proposal", signal.get("trader_proposal", ""))
    _print_report_section("Bull Research",   signal.get("bull_research", ""))
    _print_report_section("Bear Research",   signal.get("bear_research", ""))
    _print_report_section("Market / Technical Analysis", signal.get("market_report", ""))
    _print_report_section("Fundamentals Analysis", signal.get("fundamentals_report", ""))
    _print_report_section("News Analysis", signal.get("news_report", ""))
    _print_report_section("Sentiment Analysis", signal.get("sentiment_report", ""))
    _print_report_section("Fund Holdings Analysis", signal.get("holdings_report", ""))
    _print_report_section("Fund Category Analysis", signal.get("category_report", ""))


def interactive() -> None:
    console.print(Panel.fit(
        "[bold cyan]TradingAgents[/bold cyan]  Multi-agent LLM investment analysis",
        border_style="cyan",
    ))
    console.print()

    provider              = _ask_provider()
    deep_model, quick_model = _ask_model(provider)
    asset_type            = _ask_asset()
    ticker                = _ask_ticker(asset_type)
    trade_date            = _ask_date()
    invest_rounds, risk_rounds = _ask_rounds()

    config = {
        "llm_provider":            provider,
        "deep_think_llm":          deep_model,
        "quick_think_llm":         quick_model,
        "asset_type":              asset_type,
        "max_debate_rounds":       invest_rounds,
        "max_risk_discuss_rounds": risk_rounds,
    }

    console.print()
    console.print(f"[dim]Running analysis for [bold]{ticker}[/bold] on {trade_date}...[/dim]")
    console.print()

    try:
        with console.status("[bold green]Agents working...[/bold green]", spinner="dots"):
            signal = graph_run(ticker, trade_date, config)
        _display_results(signal)
        report_path = save_report(signal)
        console.print(f"[dim]Report saved → [bold]{report_path}[/bold][/dim]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
    except Exception as exc:
        console.print(f"\n[bold red]Error:[/bold red] {exc}")
        raise


if __name__ == "__main__":
    interactive()
