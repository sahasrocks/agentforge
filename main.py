"""TradingAgents entry point.

Interactive mode:   python main.py
CLI mode:           python main.py TICKER DATE [OPTIONS]
"""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console

app     = typer.Typer(add_completion=False, help="TradingAgents — multi-agent LLM investment analysis.")
console = Console()


@app.command()
def analyse(
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g. RELIANCE.NS) or MFApi scheme code."),
    trade_date: str = typer.Argument(..., help="Analysis date in YYYY-MM-DD format."),
    provider: str       = typer.Option("openai",    "--provider",    "-p",  help="LLM provider."),
    deep_model: str     = typer.Option("gpt-4o",    "--deep-model",  "-d",  help="Deep-think model."),
    quick_model: str    = typer.Option("gpt-4o-mini","--quick-model","-q",  help="Quick-think model."),
    asset_type: str     = typer.Option("stock",     "--asset-type",  "-a",  help="'stock' or 'mutual_fund'."),
    invest_rounds: int  = typer.Option(1,           "--invest-rounds",      help="Investment debate rounds."),
    risk_rounds: int    = typer.Option(1,           "--risk-rounds",        help="Risk debate rounds."),
    json_out: bool      = typer.Option(False,       "--json",               help="Output raw JSON signal."),
) -> None:
    """Run TradingAgents analysis for a single ticker in non-interactive CLI mode."""
    from tradingagents.graph.trading_graph import run as graph_run

    config = {
        "llm_provider":            provider,
        "deep_think_llm":          deep_model,
        "quick_think_llm":         quick_model,
        "asset_type":              asset_type,
        "max_debate_rounds":       invest_rounds,
        "max_risk_discuss_rounds": risk_rounds,
    }

    console.print(f"[dim]Analysing [bold]{ticker}[/bold] ({asset_type}) on {trade_date}...[/dim]")

    try:
        with console.status("[bold green]Agents working...[/bold green]", spinner="dots"):
            signal = graph_run(ticker, trade_date, config)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if json_out:
        import json
        typer.echo(json.dumps(signal, indent=2, default=str))
        return

    from rich.panel import Panel
    from rich.text import Text

    rating = signal.get("rating", "Hold")
    colours = {"Buy": "bold green", "Overweight": "green", "Hold": "yellow",
               "Underweight": "red", "Sell": "bold red"}
    colour = colours.get(rating, "white")

    header = Text()
    header.append(f"{ticker}  ", style="bold white")
    header.append(f"[{trade_date}]  ", style="dim")
    header.append(f"Rating: {rating}", style=colour)

    console.print()
    console.print(Panel(header, title="TradingAgents Result", border_style=colour))
    console.print()

    final = signal.get("final_decision", "")
    if final:
        console.print(Panel(final.strip(), title="Final Decision", border_style="blue"))


def main() -> None:
    # No arguments → launch the interactive TUI
    if len(sys.argv) == 1:
        from run_app import interactive
        interactive()
        return

    # Otherwise hand off to typer's CLI parser
    app()


if __name__ == "__main__":
    main()
