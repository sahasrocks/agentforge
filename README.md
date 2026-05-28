# TradingAgents

A multi-agent LLM framework for investment analysis. Stocks and Indian mutual funds are analysed by a pipeline of specialised agents that debate, challenge each other, and converge on a final portfolio decision.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Agents Reference](#agents-reference)
- [Data Vendors](#data-vendors)
- [LLM Providers](#llm-providers)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output & Reports](#output--reports)
- [Memory System](#memory-system)
- [Environment Variables](#environment-variables)

---

## Overview

TradingAgents orchestrates a multi-stage pipeline where:

1. **Analyst agents** independently gather market, fundamental, news, and sentiment data
2. **Bull and Bear researchers** debate the investment thesis across configurable rounds
3. **Research Manager** judges the debate and produces a rated investment plan
4. **Trader** converts the plan into a concrete trade proposal (entry, stop-loss, sizing)
5. **Risk debaters** (Aggressive / Conservative / Neutral) stress-test the proposal
6. **Portfolio Manager** issues the final 5-tier rating and executive decision

Every run saves a Markdown report to `reports/` and persists the decision to a memory store for future context injection.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     run_app.py / main.py                            │
│                  Interactive TUI  |  Typer CLI                      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  graph_run(ticker, date, config)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     trading_graph.py                                │
│  load_past_context()  →  build_graph()  →  invoke()                 │
│  →  extract_final_signal()  →  reflect_and_store()  →  save_report()│
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                             │
│                                                                     │
│   START ──fan-out──► Analyst Layer (run in parallel)                │
│                           │                                         │
│                      fan-in ──► Investment Debate Loop              │
│                                       │                             │
│                                Research Manager                     │
│                                       │                             │
│                                    Trader                           │
│                                       │                             │
│                               Risk Debate Loop                      │
│                                       │                             │
│                            Portfolio Manager ──► END                │
└─────────────────────────────────────────────────────────────────────┘
```

### Shared State

All agents share a single `AgentState` TypedDict flowing through every node:

```
AgentState
├── Identity        : company_of_interest, asset_type, trade_date
├── Analyst outputs : market_report, fundamentals_report, news_report,
│                    sentiment_report, holdings_report, category_report
├── Invest debate   : investment_debate_state
│                      { bull_history, bear_history, history,
│                        current_response, judge_decision, count }
├── Research plan   : investment_plan
├── Trade proposal  : trader_investment_plan
├── Risk debate     : risk_debate_state
│                      { aggressive_history, conservative_history,
│                        neutral_history, history, latest_speaker,
│                        judge_decision, count }
├── Final decision  : final_trade_decision
└── Memory          : past_context
```

---

## Agent Pipeline

### Stocks

```
START
  ├──► market_analyst        (OHLCV + RSI, MACD, Bollinger, SMA, ATR)
  ├──► fundamentals_analyst  (P/E, balance sheet, cash flow, income stmt)
  ├──► news_analyst          (company + global macro news)
  └──► sentiment_analyst     (Reddit, StockTwits, Google Trends, Fear & Greed)
         │  (all 4 finish before the next stage — LangGraph fan-in)
         ▼
       bull_researcher ◄──────────────────────────────────┐
         │                                                │
         │ count < max_debate_rounds × 2                 │
         ▼                                                │
       bear_researcher ──────────────────────────────────┘
         │ count >= max_debate_rounds × 2
         ▼
       research_manager  ──►  investment_plan  (ResearchPlan)
         │
         ▼
       trader  ──►  trader_investment_plan  (TraderProposal)
         │
         ▼
       aggressive_debator ◄──────────────────────────────────────────┐
         │                                                            │
         ▼                                                            │
       conservative_debator                                           │
         │                                                            │
         ▼                                                            │
       neutral_debator ──────────────────────────────────────────────┘
         │ count >= max_risk_discuss_rounds × 3
         ▼
       portfolio_manager  ──►  final_trade_decision  (PortfolioDecision)
         │
        END
```

### Mutual Funds

```
START
  ├──► holdings_analyst  (NAV history, fund info, trailing returns vs benchmark)
  ├──► category_analyst  (peer funds in same SEBI category)
  └──► news_analyst      (fund + macro news)
         │
         ▼
       [same debate + risk pipeline as stocks]
```

### Debate Loop Mechanics

**Investment debate** (`investment_debate_state.count`):
- Each count increment = one speaker turn
- Full round = bull (+1) + bear (+1) = 2 increments
- Exits to `research_manager` when `count >= max_debate_rounds × 2`
- Default: 1 round (1 bull turn + 1 bear turn)

**Risk debate** (`risk_debate_state.count`):
- Fixed rotation: Aggressive → Conservative → Neutral → Aggressive …
- Full round = 3 increments (one per speaker)
- Exits to `portfolio_manager` when `count >= max_risk_discuss_rounds × 3`
- Default: 1 round (1 turn each)

---

## Agents Reference

### Analyst Layer

| Agent | Asset | Tools | Output Key |
|---|---|---|---|
| `market_analyst` | Stock | `get_stock_data`, `get_technical_indicators` | `market_report` |
| `fundamentals_analyst` | Stock | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` | `fundamentals_report` |
| `news_analyst` | Both | `get_news`, `get_global_news` | `news_report` |
| `sentiment_analyst` | Stock | `get_reddit_sentiment`, `get_stocktwits_sentiment`, `get_google_trends`, `get_fear_greed` | `sentiment_report` |
| `holdings_analyst` | Mutual Fund | `get_fund_nav_history`, `get_fund_info`, `get_trailing_returns` | `holdings_report` |
| `category_analyst` | Mutual Fund | `get_fund_by_category`, `search_fund` | `category_report` |

All analysts use `run_agent_node()` which implements a **tool-calling loop with automatic fallback**:

- **Primary path** — standard LangChain bind_tools → invoke → ToolMessage → repeat until no more tool calls
- **Fallback path** — if tool-calling fails (e.g. Groq/LLaMA malformed function-call syntax), all tools are eagerly pre-fetched using state-derived arguments and the results are injected as plain text for the LLM

### Researcher Layer

| Agent | Role | Input | Output |
|---|---|---|---|
| `bull_researcher` | Argues FOR the investment | All analyst reports + bear's prior arguments | `investment_debate_state.bull_history` |
| `bear_researcher` | Argues AGAINST | All analyst reports + bull's prior arguments | `investment_debate_state.bear_history` |
| `research_manager` | Neutral judge of the debate | Full debate transcript | `investment_plan` |

### Execution Layer

| Agent | Role | Input | Output |
|---|---|---|---|
| `trader` | Translates research into a trade | `investment_plan` | `trader_investment_plan` |

**TraderProposal** (Pydantic): `action` (Buy/Hold/Sell), `reasoning`, `entry_price`, `stop_loss`, `position_sizing`

### Risk Layer

| Agent | Perspective | Output |
|---|---|---|
| `aggressive_debator` | Maximise return — push for bold positions | `risk_debate_state.aggressive_history` |
| `conservative_debator` | Minimise downside — reduce exposure | `risk_debate_state.conservative_history` |
| `neutral_debator` | Balance risk/reward objectively | `risk_debate_state.neutral_history` |
| `portfolio_manager` | Final accountable decision-maker | `final_trade_decision` |

**PortfolioDecision** (Pydantic): `rating` (5-tier), `executive_summary`, `investment_thesis`, `price_target`, `risk_factors`, `time_horizon`

### Pydantic Schemas (`agents/schemas.py`)

```python
class PortfolioRating(str, Enum):
    BUY = "Buy" | OVERWEIGHT = "Overweight" | HOLD = "Hold"
    UNDERWEIGHT = "Underweight" | SELL = "Sell"

class ResearchPlan(BaseModel):
    recommendation: PortfolioRating
    rationale: str
    strategic_actions: str

class TraderProposal(BaseModel):
    action: TraderAction          # Buy | Hold | Sell
    reasoning: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    position_sizing: Optional[str]

class PortfolioDecision(BaseModel):
    rating: PortfolioRating
    executive_summary: str
    investment_thesis: str
    price_target: Optional[float]
    risk_factors: Optional[str]
    time_horizon: Optional[str]
```

---

## Data Vendors

### News Vendors (fallback chain, tried in order)

| Priority | Vendor | Key Required | `get_news` | `get_global_news` |
|---|---|---|---|---|
| 1 | **Tavily** | `TAVILY_API_KEY` | Web search — best for any ticker/MF | 5 configurable macro queries |
| 2 | **RSS News** | None | Yahoo Finance RSS + Google News RSS | Reuters / BBC Business / Google News |
| 3 | **NewsAPI** | `NEWSAPI_KEY` | `/everything` endpoint | `/top-headlines?category=business` |
| 4 | **Finnhub** | `FINNHUB_KEY` | `/company-news` | `/news?category=general` |
| 5 | **yfinance** | None | `yf.Ticker.news` | S&P / Dow / Nasdaq proxy tickers |
| 6 | **Alpha Vantage** | `ALPHA_VANTAGE_API_KEY` | `NEWS_SENTIMENT` API | `NEWS_SENTIMENT` with macro topics |

### Sentiment Vendors (each tool routes directly to its dedicated vendor)

| Tool | Vendor | Key Required | Source |
|---|---|---|---|
| `get_reddit_sentiment` | `reddit.py` | None | r/wallstreetbets, r/investing, r/stocks (public JSON) |
| `get_stocktwits_sentiment` | `stocktwits.py` | None | StockTwits public stream API |
| `get_google_trends` | `google_trends.py` | None | Google Trends via pytrends |
| `get_fear_greed` | `fear_greed.py` | None | CNN Money Fear & Greed + Alternative.me |

### Mutual Fund Vendors

| Priority | Vendor | Key Required | Data |
|---|---|---|---|
| 1 | **MFApi** | None | NAV history, fund info, scheme search |
| 2 | **AMFI** | None | Official AMFI NAV file (amfiindia.com) |

### Stock Data Vendors

| Category | Primary | Fallback |
|---|---|---|
| OHLCV price data | yfinance | alpha_vantage |
| Technical indicators | yfinance | — |
| Fundamentals | yfinance | alpha_vantage |

### Vendor Routing (`dataflows/interface.py`)

```
route_to_vendor(method_name, *args)
  1. tool_vendors[method_name]      → direct (highest priority, no fallback needed)
  2. data_vendors[category]         → category default, then fallback chain
  3. fund_data_vendors[category]    → for nav_data / fund_info categories

Fallback chain behaviour:
  - Skip vendor if it doesn't implement the method (getattr returns None)
  - Skip vendor if it raises any exception (try next)
  - Raise RuntimeError only when ALL vendors in the chain are exhausted
```

---

## LLM Providers

| Provider | Env Key | Catalog Models |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini, o1, o1-mini, o3-mini |
| `anthropic` | `ANTHROPIC_API_KEY` | claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5 |
| `google` | `GOOGLE_API_KEY` | gemini-2.5-pro, gemini-2.0-flash, gemini-2.0-flash-lite |
| `groq` | `GROQ_API_KEY` | llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b, gemma2-9b |
| `deepseek` | `DEEPSEEK_API_KEY` | deepseek-chat, deepseek-reasoner |
| `xai` | `XAI_API_KEY` | grok-3, grok-3-mini, grok-2 |
| `openrouter` | `OPENROUTER_API_KEY` | Any model on openrouter.ai (type name manually) |
| `ollama` | None | Any locally pulled model (type name manually) |

**Two LLM roles per run:**

| Role | Used By | Default |
|---|---|---|
| Deep-think LLM | fundamentals, holdings, researchers, managers | `gpt-4o` |
| Quick-think LLM | market, news, sentiment, risk debaters | `gpt-4o-mini` |

Both roles can be set to the same model. The factory (`create_llm_client(provider, model).get_llm()`) returns a standard LangChain `BaseChatModel`, so tool-calling and structured output work uniformly across all providers.

---

## Project Structure

```
tradingagents/
├── agents/
│   ├── analysts/
│   │   ├── market_analyst.py           OHLCV + 6 technical indicators
│   │   ├── fundamentals_analyst.py     Balance sheet, cash flow, income stmt
│   │   ├── news_analyst.py             Company + global macro news
│   │   ├── sentiment_analyst.py        Reddit, StockTwits, Google Trends, Fear & Greed
│   │   ├── holdings_analyst.py         MF: NAV history + trailing returns vs benchmark
│   │   └── category_analyst.py         MF: peer fund comparison in SEBI category
│   │
│   ├── researchers/
│   │   ├── bull_researcher.py          Argues FOR — counter-debates bear each round
│   │   └── bear_researcher.py          Argues AGAINST — counter-debates bull each round
│   │
│   ├── managers/
│   │   ├── research_manager.py         Judges debate → ResearchPlan (structured output)
│   │   └── portfolio_manager.py        Final decision → PortfolioDecision (structured output)
│   │
│   ├── trader/
│   │   └── trader.py                   Research → TraderProposal (entry/stop/sizing)
│   │
│   ├── risk_mgmt/
│   │   ├── aggressive_debator.py       Maximise return perspective
│   │   ├── conservative_debator.py     Minimise risk perspective
│   │   └── neutral_debator.py          Balanced perspective
│   │
│   └── utils/
│       ├── agent_states.py             AgentState, InvestDebateState, RiskDebateState
│       ├── agent_utils.py              run_agent_node() + _prefetch_all_tools() fallback
│       ├── schemas.py                  ResearchPlan, TraderProposal, PortfolioDecision
│       ├── structured.py               invoke_structured_or_freetext(), bind_structured()
│       ├── rating.py                   parse_rating() → PortfolioRating enum
│       ├── core_stock_tools.py         @tool get_stock_data_tool
│       ├── technical_indicators_tools.py  @tool get_technical_indicators_tool
│       ├── fundamental_data_tools.py   @tool ×4 (fundamentals, balance sheet, cashflow, income)
│       ├── news_data_tools.py          @tool ×3 (news, global_news, reddit_sentiment)
│       ├── sentiment_data_tools.py     @tool ×3 (stocktwits, google_trends, fear_greed)
│       └── fund_tools.py               @tool ×5 (nav_history, fund_info, returns, search, category)
│
├── dataflows/
│   ├── interface.py                    route_to_vendor() — central dispatch + fallback chain
│   ├── config.py                       get_config() / set_config() module-level store
│   ├── utils.py                        AlphaVantageRateLimitError, shared helpers
│   │
│   ├── tavily.py                       News: Tavily web search (primary)
│   ├── rss_news.py                     News: Yahoo Finance + Google News RSS (no key)
│   ├── newsapi.py                      News: NewsAPI.org (NEWSAPI_KEY)
│   ├── finnhub.py                      News: Finnhub (FINNHUB_KEY)
│   ├── y_finance.py                    Stocks + news: yfinance
│   ├── alpha_vantage_stock.py          Stocks: Alpha Vantage
│   ├── alpha_vantage_news.py           News: Alpha Vantage NEWS_SENTIMENT
│   │
│   ├── reddit.py                       Sentiment: Reddit public JSON API (no key)
│   ├── stocktwits.py                   Sentiment: StockTwits public API (no key)
│   ├── google_trends.py                Sentiment: pytrends (no key)
│   ├── fear_greed.py                   Sentiment: CNN Money + Alternative.me (no key)
│   │
│   ├── mfapi.py                        MF: MFApi.in (primary, no key)
│   ├── amfi.py                         MF: AMFI official NAV file (no key)
│   └── stockstats_utils.py             Technical indicator helpers
│
├── graph/
│   ├── trading_graph.py                run() — top-level pipeline entry point
│   ├── setup.py                        build_graph() — assembles LangGraph StateGraph
│   ├── propagation.py                  initialise_state() — zeroed AgentState
│   ├── signal_processing.py            extract_final_signal(), save_report()
│   ├── reflection.py                   reflect_and_store(), load_past_context()
│   ├── conditional_logic.py            Debate routers (invest loop + risk loop)
│   ├── analyst_execution.py            get_analyst_node_names(asset_type)
│   └── checkpointer.py                 Optional MemorySaver for crash/resume
│
├── llm_clients/
│   ├── factory.py                      create_llm_client(provider, model)
│   ├── base_client.py                  BaseLLMClient ABC
│   ├── model_catalog.py                MODEL_CATALOG, get_all_providers()
│   ├── openai_client.py                OpenAI / xAI / DeepSeek / OpenRouter
│   ├── anthropic_client.py             Anthropic Claude
│   ├── google_client.py                Google Gemini
│   ├── groq_client.py                  Groq
│   ├── ollama_client.py                Ollama (local)
│   ├── api_key_env.py                  ensure_api_key() validation
│   └── validators.py                   validate_provider()
│
├── default_config.py                   DEFAULT_CONFIG dict + get_config()
└── __init__.py

run_app.py                              Interactive TUI (questionary + rich)
main.py                                 Entry: TUI if no args, Typer CLI otherwise
memory_store.json                       Per-ticker decision history (auto-created)
reports/                                Saved Markdown reports (auto-created)
.env                                    API keys
```

---

## Installation

**Requirements:** Python 3.10+

```bash
# 1. Clone
git clone <repo-url>
cd tradingagents

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env — at minimum set the key for your chosen LLM provider
```

---

## Configuration

All settings live in `tradingagents/default_config.py`. Every scalar key can be overridden via an environment variable using the prefix `TRADINGAGENTS_<KEY_UPPERCASE>`.

### Core Settings

```python
DEFAULT_CONFIG = {
    # LLM selection
    "llm_provider":    "openai",
    "deep_think_llm":  "gpt-4o",        # analysts + researchers + managers
    "quick_think_llm": "gpt-4o-mini",   # market, news, sentiment, risk debaters

    # Debate depth
    "max_debate_rounds":       1,        # bull+bear turns = 2 × this
    "max_risk_discuss_rounds": 1,        # agg+con+neu turns = 3 × this

    # Asset type
    "asset_type": "stock",              # "stock" | "mutual_fund"

    # Primary data vendors per category
    "data_vendors": {
        "core_stock_apis":      "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data":     "yfinance",
        "news_data":            "tavily",   # primary news source
        "sentiment_data":       "reddit",
    },

    # Direct vendor routing for single-vendor sentiment tools
    "tool_vendors": {
        "get_reddit_sentiment":     "reddit",
        "get_stocktwits_sentiment": "stocktwits",
        "get_google_trends":        "google_trends",
        "get_fear_greed":           "fear_greed",
    },

    # Mutual fund vendors
    "fund_data_vendors": {
        "nav_data":  "mfapi",
        "fund_info": "mfapi",
    },
}
```

### Runtime Overrides via Environment

```bash
TRADINGAGENTS_LLM_PROVIDER=anthropic
TRADINGAGENTS_DEEP_THINK_LLM=claude-sonnet-4-6
TRADINGAGENTS_QUICK_THINK_LLM=claude-haiku-4-5-20251001
TRADINGAGENTS_MAX_DEBATE_ROUNDS=2
TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS=2
TRADINGAGENTS_ASSET_TYPE=mutual_fund
TRADINGAGENTS_CHECKPOINT_ENABLED=true
```

---

## Usage

### Interactive TUI

```bash
python main.py
# or
python run_app.py
```

Guided prompts walk through: provider → model (deep + quick) → asset type → ticker → date → debate rounds.

### CLI (Non-interactive)

```bash
# Stock
python main.py RELIANCE.NS 2026-05-27 \
  --provider anthropic \
  --deep-model claude-sonnet-4-6 \
  --quick-model claude-haiku-4-5-20251001 \
  --invest-rounds 2 --risk-rounds 1

# Indian mutual fund
python main.py 119598 2026-05-27 \
  --asset-type mutual_fund \
  --provider openai \
  --deep-model gpt-4o --quick-model gpt-4o-mini

# JSON output for programmatic use
python main.py AAPL 2026-05-27 --json
```

### Python API

```python
from tradingagents.graph.trading_graph import run

config = {
    "llm_provider":            "openai",
    "deep_think_llm":          "gpt-4o",
    "quick_think_llm":         "gpt-4o-mini",
    "asset_type":              "stock",
    "max_debate_rounds":       1,
    "max_risk_discuss_rounds": 1,
}

signal = run("RELIANCE.NS", "2026-05-27", config)

print(signal["rating"])           # "Buy" | "Overweight" | "Hold" | "Underweight" | "Sell"
print(signal["final_decision"])   # Full markdown executive decision
print(signal["bull_research"])    # Bull researcher's accumulated arguments
print(signal["bear_research"])    # Bear researcher's accumulated arguments
print(signal["investment_plan"])  # Research Manager's rated plan
print(signal["trader_proposal"])  # Trader's entry / stop-loss / sizing
print(signal["market_report"])    # Technical analysis (stocks only)
print(signal["sentiment_report"]) # Social sentiment (stocks only)
print(signal["holdings_report"])  # NAV & returns (mutual funds only)
```

---

## Output & Reports

### Signal Dict Keys

| Key | Description |
|---|---|
| `ticker` | Asset identifier |
| `asset_type` | `"stock"` or `"mutual_fund"` |
| `trade_date` | Analysis date |
| `rating` | Final 5-tier rating |
| `final_decision` | Portfolio Manager's full markdown decision |
| `investment_plan` | Research Manager's plan after the bull/bear debate |
| `trader_proposal` | Trader's entry / stop-loss / position-sizing proposal |
| `bull_research` | Bull researcher's accumulated debate arguments |
| `bear_research` | Bear researcher's accumulated debate arguments |
| `market_report` | Market & technical analysis *(stocks)* |
| `fundamentals_report` | Fundamentals analysis *(stocks)* |
| `news_report` | News analysis *(both asset types)* |
| `sentiment_report` | Social sentiment analysis *(stocks)* |
| `holdings_report` | NAV history & trailing returns *(mutual funds)* |
| `category_report` | Peer fund category analysis *(mutual funds)* |

### Saved Report Format

Reports are written to `reports/<TICKER>_<DATE>.md`:

```
reports/
├── RELIANCE_NS_2026-05-27.md
├── AAPL_2026-05-26.md
└── 119598_2026-05-25.md
```

Each report contains:
```markdown
# TradingAgents Report — TICKER

| Field | Value |
| Rating | **Buy** |

## Final Portfolio Decision
## Investment Plan
## Trader Proposal
## Bull Research
## Bear Research
## Market / Technical Analysis
## Fundamentals Analysis
## News Analysis
## Sentiment Analysis
## Fund Holdings Analysis    ← mutual funds only
## Fund Category Analysis    ← mutual funds only
```

---

## Memory System

After every run, `reflect_and_store()` appends the outcome to `memory_store.json`:

```json
{
  "RELIANCE.NS": [
    {
      "trade_date":     "2026-05-27",
      "rating":         "Buy",
      "final_decision": "...",
      "stored_at":      "2026-05-27T10:30:00"
    }
  ]
}
```

At the start of the **next run** for the same ticker, `load_past_context()` reads the last 5 entries within the lookback window and injects them into the first human message that every agent receives — letting agents explicitly account for recent rating drift or changed thesis.

| Asset Type | Lookback Window |
|---|---|
| Stock | 5 days |
| Mutual Fund | 30 days |

---

## Environment Variables

### LLM Provider Keys

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
XAI_API_KEY=xai-...
OPENROUTER_API_KEY=sk-or-...
```

### Data Vendor Keys

```env
# Primary news — strongly recommended
TAVILY_API_KEY=tvly-...

# Optional news fallbacks
NEWSAPI_KEY=...               # newsapi.org  — 100 req/day free tier
FINNHUB_KEY=...               # finnhub.io   — 60 calls/min free tier
ALPHA_VANTAGE_API_KEY=...     # alphavantage.co — 25 req/day free tier

# The following need NO key:
#   RSS feeds, Reddit, StockTwits, Google Trends,
#   Fear & Greed Index, yfinance, MFApi, AMFI
```

---

## Supported Assets

| Market | Format | Example |
|---|---|---|
| US stocks | Plain symbol | `AAPL`, `TSLA`, `NVDA` |
| Indian NSE | Symbol + `.NS` | `RELIANCE.NS`, `TCS.NS`, `INFY.NS` |
| Indian BSE | Symbol + `.BO` | `RELIANCE.BO` |
| Indian mutual funds | MFApi scheme code | `119598`, `105758` |
| Australian | Symbol + `.AX` | `RIO.AX` |
| London | Symbol + `.L` | `BA.L` |
| Japan | Symbol + `.T` | `7203.T` |
| Hong Kong | Symbol + `.HK` | `9988.HK` |

To find an Indian mutual fund scheme code: `mfapi.in/mf/search?q=<fund-name>`
