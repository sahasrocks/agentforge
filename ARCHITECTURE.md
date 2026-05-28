# TradingAgents — Full Architecture Reference

> A multi-agent LLM financial trading framework built on LangGraph.  
> Use this document as a blueprint to recreate the project.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Layout](#3-repository-layout)
4. [High-Level Pipeline](#4-high-level-pipeline)
5. [State Schema](#5-state-schema)
6. [LangGraph Flow](#6-langgraph-flow)
7. [Agent Catalogue](#7-agent-catalogue)
8. [Tool System](#8-tool-system)
9. [Data Layer](#9-data-layer)
10. [LLM Client Layer](#10-llm-client-layer)
11. [Memory & Reflection System](#11-memory--reflection-system)
12. [Structured Output Strategy](#12-structured-output-strategy)
13. [Configuration System](#13-configuration-system)
14. [CLI Architecture](#14-cli-architecture)
15. [Checkpoint / Resume](#15-checkpoint--resume)
16. [Error Handling & Fallbacks](#16-error-handling--fallbacks)
17. [End-to-End Execution Flow](#17-end-to-end-execution-flow)
18. [Key Design Decisions](#18-key-design-decisions)

---

## 1. Project Overview

TradingAgents simulates how a real trading firm works by deploying specialized LLM-powered agents that mirror distinct roles: analysts who gather data, researchers who debate, a trader who proposes a transaction, risk managers who stress-test it, and a portfolio manager who makes the final call.

**Core value proposition:**
- Structured adversarial debate (bull vs bear, aggressive vs conservative) to prevent groupthink
- Provider-agnostic: same code runs on OpenAI, Gemini, Claude, DeepSeek, Ollama, etc.
- 5-tier rating scale: **Buy / Overweight / Hold / Underweight / Sell**
- Memory log: learns from past decisions once outcomes are known (deferred reflection)

---

## 2. Tech Stack

| Layer | Library / Tool |
|---|---|
| Agent orchestration | `langgraph >= 0.4.8` |
| LLM abstraction | `langchain-core`, `langchain-openai`, `langchain-anthropic`, `langchain-google-genai` |
| Data — price/fundamentals | `yfinance`, `stockstats` (technical indicators) |
| Data — news/sentiment | `yfinance news`, `StockTwits public API`, `Reddit public JSON API` |
| Data — fundamentals (alt) | `alpha_vantage` (optional, fallback vendor) |
| Structured output | `pydantic v2` (BaseModel schemas) |
| CLI / TUI | `typer`, `questionary`, `rich` |
| Checkpoint storage | `langgraph-checkpoint-sqlite` (per-ticker SQLite) |
| Environment | `python-dotenv` |
| Packaging | `pyproject.toml`, `setuptools` |

---

## 3. Repository Layout

```
TradingAgents/
├── cli/                          # Interactive CLI / TUI
│   ├── main.py                   # Typer app, Rich live display, prompt loop
│   ├── utils.py                  # questionary prompt helpers
│   ├── models.py                 # AnalystType, AssetType enums
│   ├── stats_handler.py          # LangChain callback for token/call counting
│   └── static/welcome.txt        # ASCII art splash
│
├── tradingagents/
│   ├── default_config.py         # Single source of truth for all config keys
│   │
│   ├── graph/                    # LangGraph orchestration
│   │   ├── trading_graph.py      # TradingAgentsGraph — top-level entry point
│   │   ├── setup.py              # GraphSetup — builds nodes + edges
│   │   ├── propagation.py        # Propagator — state init + graph args
│   │   ├── conditional_logic.py  # ConditionalLogic — flow control functions
│   │   ├── reflection.py         # Reflector — post-hoc outcome reflections
│   │   ├── signal_processing.py  # SignalProcessor — extract rating from text
│   │   ├── analyst_execution.py  # Analyst ordering, wall-time tracking
│   │   └── checkpointer.py       # SQLite checkpoint helpers
│   │
│   ├── agents/
│   │   ├── analysts/
│   │   │   ├── market_analyst.py       # Technical indicators, OHLCV
│   │   │   ├── sentiment_analyst.py    # News + StockTwits + Reddit (pre-fetch)
│   │   │   ├── news_analyst.py         # Company + macro news (tool-calling)
│   │   │   └── fundamentals_analyst.py # Financial statements (tool-calling)
│   │   ├── researchers/
│   │   │   ├── bull_researcher.py      # Bullish argument
│   │   │   └── bear_researcher.py      # Bearish argument
│   │   ├── managers/
│   │   │   ├── research_manager.py     # Debate judge → ResearchPlan
│   │   │   └── portfolio_manager.py    # Final decision → PortfolioDecision
│   │   ├── trader/
│   │   │   └── trader.py               # Transaction proposal → TraderProposal
│   │   ├── risk_mgmt/
│   │   │   ├── aggressive_debator.py
│   │   │   ├── conservative_debator.py
│   │   │   └── neutral_debator.py
│   │   ├── utils/
│   │   │   ├── agent_states.py         # TypedDicts: AgentState, InvestDebateState, RiskDebateState
│   │   │   ├── agent_utils.py          # Tool exports, language instruction, instrument context
│   │   │   ├── core_stock_tools.py     # @tool get_stock_data
│   │   │   ├── technical_indicators_tools.py  # @tool get_indicators
│   │   │   ├── fundamental_data_tools.py      # @tool get_fundamentals / balance_sheet / etc.
│   │   │   ├── news_data_tools.py      # @tool get_news / get_global_news / get_insider_transactions
│   │   │   ├── memory.py               # TradingMemoryLog — append-only decision log
│   │   │   ├── rating.py               # parse_rating() — deterministic 5-tier extraction
│   │   │   └── structured.py           # bind_structured, invoke_structured_or_freetext
│   │   └── schemas.py                  # Pydantic output schemas
│   │
│   ├── dataflows/                # Data vendor abstraction
│   │   ├── interface.py          # route_to_vendor — vendor-agnostic routing
│   │   ├── config.py             # get_config / set_config — global dataflow config
│   │   ├── y_finance.py          # yfinance implementation
│   │   ├── stockstats_utils.py   # stockstats indicator calculations
│   │   ├── stocktwits.py         # StockTwits public API scraper
│   │   ├── reddit.py             # Reddit public JSON API scraper
│   │   ├── alpha_vantage*.py     # Alpha Vantage implementations (stock, news, indicators, fundamentals)
│   │   └── utils.py              # safe_ticker_component, date helpers
│   │
│   └── llm_clients/              # Provider abstraction
│       ├── factory.py            # create_llm_client() — lazy provider loader
│       ├── base_client.py        # BaseLLMClient, normalize_content()
│       ├── capabilities.py       # Per-model capability table (tool_choice, json_mode, etc.)
│       ├── model_catalog.py      # CLI model dropdown options per provider
│       ├── api_key_env.py        # provider → env var name mapping
│       ├── validators.py         # Model name validation
│       ├── openai_client.py      # OpenAI + all OpenAI-compatible providers
│       ├── anthropic_client.py   # Anthropic Claude
│       ├── google_client.py      # Google Gemini
│       └── azure_client.py       # Azure OpenAI
│
├── main.py                       # Minimal programmatic entry point
├── run_app.py                    # Non-interactive smoke-test runner
├── pyproject.toml
├── Dockerfile / docker-compose.yml
└── .env.example
```

---

## 4. High-Level Pipeline

```
User Input
  (ticker, date, analysts, provider, model)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    TradingAgentsGraph                        │
│                                                             │
│  1. Resolve pending memory entries (fetch outcomes)         │
│  2. Load past_context from memory log                       │
│  3. Execute LangGraph pipeline                              │
│  4. Store new decision to memory log (pending)              │
│  5. Extract 5-tier rating                                   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                   │
│                                                             │
│  Phase 1: Analyst Team (parallel data gathering)            │
│    ├── Market Analyst    → market_report                    │
│    ├── Sentiment Analyst → sentiment_report                 │
│    ├── News Analyst      → news_report                      │
│    └── Fundamentals Analyst → fundamentals_report           │
│                                                             │
│  Phase 2: Investment Debate                                 │
│    ├── Bull Researcher ─┐                                   │
│    └── Bear Researcher ◄┘ (alternates N rounds)             │
│    └── Research Manager → investment_plan (ResearchPlan)    │
│                                                             │
│  Phase 3: Trader                                            │
│    └── Trader → trader_investment_plan (TraderProposal)     │
│                                                             │
│  Phase 4: Risk Debate                                       │
│    ├── Aggressive Analyst ─┐                                │
│    ├── Conservative Analyst│ (cycles N rounds)              │
│    └── Neutral Analyst   ◄─┘                                │
│    └── Portfolio Manager → final_trade_decision             │
│                                                             │
│  Output: rating (Buy/Overweight/Hold/Underweight/Sell)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. State Schema

The entire pipeline shares one `AgentState` dict (LangGraph `MessagesState` subclass).

### AgentState (TypedDict)

```python
class AgentState(MessagesState):
    # Identity
    company_of_interest: str        # ticker symbol, e.g. "AAPL"
    asset_type: str                 # "stock" | "crypto"
    trade_date: str                 # "YYYY-MM-DD"
    sender: str                     # last agent name

    # Analyst outputs
    market_report: str
    sentiment_report: str
    news_report: str
    fundamentals_report: str

    # Investment debate
    investment_debate_state: InvestDebateState
    investment_plan: str            # Research Manager's final markdown

    # Trading
    trader_investment_plan: str     # Trader's markdown proposal

    # Risk debate
    risk_debate_state: RiskDebateState
    final_trade_decision: str       # Portfolio Manager's final markdown

    # Memory injection
    past_context: str               # Prior decisions for same + cross ticker
```

### InvestDebateState (TypedDict)

```python
{
    "bull_history": str,        # Bull's cumulative arguments
    "bear_history": str,        # Bear's cumulative arguments
    "history": str,             # Combined debate transcript
    "current_response": str,    # Latest message
    "judge_decision": str,      # Research Manager decision
    "count": int,               # Round counter (terminates at 2 * max_debate_rounds)
}
```

### RiskDebateState (TypedDict)

```python
{
    "aggressive_history": str,
    "conservative_history": str,
    "neutral_history": str,
    "history": str,
    "latest_speaker": str,                      # "Aggressive" | "Conservative" | "Neutral"
    "current_aggressive_response": str,
    "current_conservative_response": str,
    "current_neutral_response": str,
    "judge_decision": str,                      # Portfolio Manager decision
    "count": int,                               # Terminates at 3 * max_risk_discuss_rounds
}
```

---

## 6. LangGraph Flow

### Node Map

```
START
  │
  ▼
[Market Analyst] ──► [tools_market] ──► (loop)
  │ (no tool calls)
  ▼
[Msg Clear Market]
  │
  ▼
[News Analyst] ──► [tools_news] ──► (loop)
  │ (no tool calls)
  ▼
[Msg Clear News]
  │
  ▼
  ... (same for Sentiment, Fundamentals if selected)
  │
  ▼
[Bull Researcher] ◄──────────────────┐
  │                                   │ count < 2*max_debate_rounds
  ▼                                   │
[Bear Researcher] ───────────────────┘
  │ count >= 2*max_debate_rounds
  ▼
[Research Manager]
  │
  ▼
[Trader]
  │
  ▼
[Aggressive Analyst] ◄────────────────────────┐
  │                                            │
  ▼                                            │
[Conservative Analyst]                         │ count < 3*max_risk_discuss_rounds
  │                                            │
  ▼                                            │
[Neutral Analyst] ─────────────────────────────┘
  │ count >= 3*max_risk_discuss_rounds
  ▼
[Portfolio Manager]
  │
  ▼
END
```

### Edge Types

| Edge | Type | Logic |
|---|---|---|
| Analyst → tools or clear | Conditional | `last_message.tool_calls` present? → tools; else → clear |
| Debate routing | Conditional | `current_response.startswith("Bull")` → Bear; else → Bull; count threshold → Research Manager |
| Risk routing | Conditional | `latest_speaker == "Aggressive"` → Conservative; `"Conservative"` → Neutral; `"Neutral"` → Aggressive; count threshold → Portfolio Manager |
| All others | Direct | Fixed edges |

---

## 7. Agent Catalogue

### Analyst Team

| Agent | File | Tools | Strategy |
|---|---|---|---|
| Market Analyst | `market_analyst.py` | `get_stock_data`, `get_indicators` | Tool-calling loop; selects up to 8 complementary indicators |
| Sentiment Analyst | `sentiment_analyst.py` | None (pre-fetch) | Injects StockTwits + Reddit + news as context blocks; single LLM call |
| News Analyst | `news_analyst.py` | `get_news`, `get_global_news` | Tool-calling loop; company + macro news |
| Fundamentals Analyst | `fundamentals_analyst.py` | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` | Tool-calling loop; financial statements |

### Researcher Team

| Agent | File | Input | Output |
|---|---|---|---|
| Bull Researcher | `bull_researcher.py` | 4 analyst reports + debate history | Bullish argument appended to `investment_debate_state` |
| Bear Researcher | `bear_researcher.py` | 4 analyst reports + debate history | Bearish argument appended to `investment_debate_state` |
| Research Manager | `research_manager.py` | Full debate history | `ResearchPlan` → `investment_plan` |

### Trading Team

| Agent | File | Input | Output |
|---|---|---|---|
| Trader | `trader.py` | `investment_plan` + analyst reports | `TraderProposal` → `trader_investment_plan` |

### Risk Management

| Agent | File | Role |
|---|---|---|
| Aggressive Analyst | `aggressive_debator.py` | Champions high-reward/high-risk; challenges caution |
| Conservative Analyst | `conservative_debator.py` | Protects capital; minimizes volatility |
| Neutral Analyst | `neutral_debator.py` | Balanced synthesis of both perspectives |
| Portfolio Manager | `portfolio_manager.py` | Final arbiter → `PortfolioDecision` → `final_trade_decision` |

---

## 8. Tool System

### Tool Definitions

All tools are LangChain `@tool` decorated functions that route to the configured vendor.

```python
@tool
def get_stock_data(symbol: str, start_date: str, end_date: str) -> str:
    """Retrieve OHLCV historical price data."""

@tool
def get_indicators(symbol: str, indicator: str, curr_date: str, look_back_days: int = 30) -> str:
    """Retrieve technical indicator(s). indicator can be comma-separated."""

@tool
def get_fundamentals(ticker: str, curr_date: str) -> str:
    """Company overview, valuation ratios, financial health metrics."""

@tool
def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str

@tool
def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str

@tool
def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str

@tool
def get_news(ticker: str, start_date: str, end_date: str) -> str

@tool
def get_global_news(curr_date: str, look_back_days: int = None, limit: int = None) -> str

@tool
def get_insider_transactions(ticker: str) -> str
```

### Tool Nodes per Analyst

```python
tool_nodes = {
    "tools_market":       ToolNode([get_stock_data, get_indicators]),
    "tools_social":       ToolNode([get_news]),
    "tools_news":         ToolNode([get_news, get_global_news, get_insider_transactions]),
    "tools_fundamentals": ToolNode([get_fundamentals, get_balance_sheet,
                                    get_cashflow, get_income_statement]),
}
```

### Supported Technical Indicators

`close_50_sma`, `close_200_sma`, `close_10_ema`, `macd`, `macds`, `macdh`, `rsi`, `boll`, `boll_ub`, `boll_lb`, `atr`, `vwma`, `mfi`

---

## 9. Data Layer

### Vendor Routing (`dataflows/interface.py`)

```
Tool Call
    │
    ▼
route_to_vendor(method, *args)
    │
    ├── Look up vendor from config["tool_vendors"] (tool-level override)
    │   or config["data_vendors"] (category-level default)
    │
    ├── Build fallback chain: [primary] + [all other vendors]
    │
    └── Try each vendor in order:
            yfinance → success ✓
            alpha_vantage → AlphaVantageRateLimitError → next
            RuntimeError if all fail
```

### Data Sources

| Source | Library | Auth | Used By |
|---|---|---|---|
| yfinance | `yfinance` | None | Price, fundamentals, news (default) |
| StockTwits | HTTP GET (public) | None | Sentiment Analyst |
| Reddit | HTTP GET (public JSON) | None | Sentiment Analyst |
| Alpha Vantage | REST API | `ALPHA_VANTAGE_API_KEY` | All (optional fallback) |
| stockstats | `stockstats` | None | Technical indicator calculation |

### Vendor Config

```python
config["data_vendors"] = {
    "core_stock_apis":    "yfinance",    # get_stock_data
    "technical_indicators": "yfinance",  # get_indicators
    "fundamental_data":   "yfinance",    # get_fundamentals, balance_sheet, etc.
    "news_data":          "yfinance",    # get_news, get_global_news, etc.
}
# Tool-level override (takes precedence):
config["tool_vendors"] = {
    # "get_stock_data": "alpha_vantage"  # example override
}
```

---

## 10. LLM Client Layer

### Factory Pattern

```python
# factory.py
def create_llm_client(provider, model, base_url=None, **kwargs) -> BaseLLMClient:
    # Lazy imports — only loads SDK for selected provider
    match provider:
        case "openai" | "xai" | "deepseek" | "qwen" | "glm" | "minimax" | "ollama" | "openrouter":
            from .openai_client import OpenAIClient
            return OpenAIClient(model, base_url, **kwargs)
        case "anthropic":
            from .anthropic_client import AnthropicClient
            return AnthropicClient(model, **kwargs)
        case "google":
            from .google_client import GoogleClient
            return GoogleClient(model, **kwargs)
        case "azure":
            from .azure_client import AzureClient
            return AzureClient(model, base_url, **kwargs)
```

### Supported Providers

| Provider key | SDK | API Key Env Var |
|---|---|---|
| `openai` | `langchain-openai` | `OPENAI_API_KEY` |
| `anthropic` | `langchain-anthropic` | `ANTHROPIC_API_KEY` |
| `google` | `langchain-google-genai` | `GOOGLE_API_KEY` |
| `xai` | `langchain-openai` (OpenAI-compat) | `XAI_API_KEY` |
| `deepseek` | `langchain-openai` (OpenAI-compat) | `DEEPSEEK_API_KEY` |
| `qwen` / `qwen-cn` | `langchain-openai` (OpenAI-compat) | `DASHSCOPE_API_KEY` / `DASHSCOPE_CN_API_KEY` |
| `glm` / `glm-cn` | `langchain-openai` (OpenAI-compat) | `ZHIPU_API_KEY` / `ZHIPU_CN_API_KEY` |
| `minimax` / `minimax-cn` | `langchain-openai` (OpenAI-compat) | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` |
| `openrouter` | `langchain-openai` (OpenAI-compat) | `OPENROUTER_API_KEY` |
| `ollama` | `langchain-openai` (OpenAI-compat) | None |
| `azure` | Azure OpenAI SDK | Azure credentials |

### Two LLM Roles

```python
# TradingAgentsGraph uses two LLM instances:
quick_llm = create_llm_client(provider, config["quick_think_llm"], ...)  # lightweight tasks
deep_llm  = create_llm_client(provider, config["deep_think_llm"],  ...)  # complex reasoning

# Assignment:
# Analysts         → deep_llm (tool-calling, complex analysis)
# Researchers      → deep_llm (debate, counterargument)
# Managers/Trader  → deep_llm (structured output, final decision)
# Reflector        → quick_llm (2-4 sentence reflection)
```

### Capability Table

Per-model capabilities control structured output strategy and API quirks:

```python
@dataclass(frozen=True)
class ModelCapabilities:
    supports_tool_choice: bool
    supports_json_mode: bool
    supports_json_schema: bool
    preferred_structured_method: str    # "function_calling" | "json_mode" | "json_schema" | "none"
    requires_reasoning_content_roundtrip: bool  # DeepSeek thinking
    requires_reasoning_split: bool              # MiniMax M2.x
```

### Response Normalization

```python
def normalize_content(response):
    # Handles providers that return content as list of typed blocks
    # (OpenAI Responses API, Google Gemini 3.x)
    # Extracts and concatenates text blocks, discards reasoning metadata
```

---

## 11. Memory & Reflection System

### Architecture

```
TradingMemoryLog
  │
  ├── memory_log_path: ~/.tradingagents/memory/trading_memory.md
  │
  ├── Phase A (write at run end):
  │   store_decision(ticker, date, final_trade_decision)
  │   → Appends [DATE | TICKER | RATING | pending] entry
  │
  ├── Phase A (read at run start):
  │   get_past_context(ticker, n_same=5, n_cross=3)
  │   → Returns last N decisions for same ticker + M cross-ticker lessons
  │   → Injected into portfolio_manager_node as state["past_context"]
  │
  └── Phase B (deferred, on next run for same ticker):
      _resolve_pending_entries(ticker)
      → Fetch real returns via yfinance (holding_days=5)
      → generate reflection via Reflector (quick_llm)
      → batch_update_with_outcomes()
      → Replaces [pending] tag with [+2.5% | +1.8% | 5d]
      → Appends REFLECTION: block
```

### Memory Log Format

```markdown
[2025-01-15 | AAPL | Buy | pending]

DECISION:
**Rating: Buy**

...full Portfolio Manager markdown...

<!-- ENTRY_END -->

[2025-01-20 | AAPL | Buy | +2.5% | +1.8% | 5d]

DECISION:
**Rating: Buy**

...

REFLECTION:
The bullish call was directionally correct (+2.5% raw, +1.8% alpha vs SPY).
The thesis around strong iPhone upgrade cycle held. The underestimated risk
was supply-chain pressure which compressed margins in Q2. For next analysis:
weight supply chain commentary more heavily when guidance references Asia.

<!-- ENTRY_END -->
```

### Rotation

When `config["memory_log_max_entries"]` is set, oldest **resolved** entries are pruned. Pending entries are never pruned.

---

## 12. Structured Output Strategy

### Pydantic Schemas

```python
class PortfolioRating(str, Enum):
    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"

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
    risk_levels: Optional[Dict[str, float]]
    time_horizon: Optional[str]
```

### Fallback Strategy

```python
def invoke_structured_or_freetext(structured_llm, plain_llm, prompt, render, agent_name):
    try:
        result = structured_llm.invoke(prompt)   # returns Pydantic instance
        return render(result)                     # → markdown string
    except Exception:
        logger.warning(f"{agent_name}: structured-output failed; retrying as free text")
        response = plain_llm.invoke(prompt)
        return response.content                   # → raw markdown string
```

All manager/trader agents use this pattern — the system always produces a string regardless of provider capability.

### Rating Extraction

```python
def parse_rating(text: str, default="Hold") -> str:
    # Pass 1: look for "Rating: X" or "rating - X" label
    # Pass 2: find first occurrence of any 5-tier rating word
    # Returns title-cased rating or default
    RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
```

---

## 13. Configuration System

### Default Config (`default_config.py`)

```python
DEFAULT_CONFIG = {
    # Paths
    "results_dir":         "~/.tradingagents/logs",
    "data_cache_dir":      "~/.tradingagents/cache",
    "memory_log_path":     "~/.tradingagents/memory/trading_memory.md",
    "memory_log_max_entries": None,       # None = no rotation

    # LLM
    "llm_provider":        "openai",
    "deep_think_llm":      "gpt-5.4",
    "quick_think_llm":     "gpt-5.4-mini",
    "backend_url":         None,          # None = provider default endpoint
    "google_thinking_level":   None,      # "high" | "minimal"
    "openai_reasoning_effort": None,      # "high" | "medium" | "low"
    "anthropic_effort":        None,      # "high" | "medium" | "low"
    "output_language":     "English",

    # Graph
    "checkpoint_enabled":       False,
    "max_debate_rounds":        1,        # Bull + Bear exchange count = 2 * this
    "max_risk_discuss_rounds":  1,        # Agg + Con + Neu cycle count = 3 * this
    "max_recur_limit":          100,
    "analyst_concurrency_limit": 1,       # Serial for now

    # News
    "news_article_limit":           20,
    "global_news_article_limit":    10,
    "global_news_lookback_days":    7,
    "global_news_queries": [
        "Federal Reserve interest rates inflation",
        "S&P 500 earnings GDP economic outlook",
        "geopolitical risk trade war sanctions",
        "ECB Bank of England BOJ central bank policy",
        "oil commodities supply chain energy",
    ],

    # Data vendors
    "data_vendors": {
        "core_stock_apis":    "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data":   "yfinance",
        "news_data":          "yfinance",
    },
    "tool_vendors": {},

    # Benchmark (for alpha calculation in memory reflection)
    "benchmark_ticker": None,
    "benchmark_map": {
        ".NS": "^NSEI", ".BO": "^BSESN", ".T": "^N225",
        ".HK": "^HSI",  ".L": "^FTSE",   ".TO": "^GSPTSE",
        ".AX": "^AXJO", "":   "SPY",
    },
}
```

### Environment Variable Overrides

Any config key can be overridden via `TRADINGAGENTS_*` env vars without code changes:

```bash
TRADINGAGENTS_LLM_PROVIDER=anthropic
TRADINGAGENTS_DEEP_THINK_LLM=claude-opus-4-7
TRADINGAGENTS_QUICK_THINK_LLM=claude-sonnet-4-6
TRADINGAGENTS_MAX_DEBATE_ROUNDS=3
TRADINGAGENTS_MAX_RISK_ROUNDS=2
TRADINGAGENTS_OUTPUT_LANGUAGE=Spanish
TRADINGAGENTS_CHECKPOINT_ENABLED=true
```

---

## 14. CLI Architecture

### Components

```
cli/main.py
  │
  ├── MessageBuffer                 # Tracks agent progress + buffers reports
  │   ├── agent_status: Dict        # "pending" | "in_progress" | "completed"
  │   ├── report_sections: Dict     # market_report, news_report, etc.
  │   ├── messages: deque           # Recent messages for live display
  │   └── tool_calls: deque         # Recent tool calls for live display
  │
  ├── get_user_selections()         # 8-step interactive questionary flow
  │   ├── Step 1: Ticker symbol
  │   ├── Step 2: Analysis date
  │   ├── Step 3: Output language
  │   ├── Step 4: Analyst selection (checkbox)
  │   ├── Step 5: Research depth (1/3/5 rounds)
  │   ├── Step 6: LLM provider
  │   ├── Step 7: Quick + deep model selection
  │   └── Step 8: Provider-specific thinking config
  │
  ├── run_analysis()                # Main analysis runner
  │   ├── Builds config from selections
  │   ├── Initializes TradingAgentsGraph
  │   ├── Starts Rich Live display
  │   ├── Streams graph chunks → updates MessageBuffer
  │   └── Post-analysis: save report, display full report
  │
  └── Rich Layout (4 panels):
      ├── header: Welcome banner
      ├── progress: Agent status table (team / agent / status)
      ├── messages: Live message + tool call feed (newest first)
      ├── analysis: Current report markdown (updates as agents complete)
      └── footer: Stats (agents N/N | LLM calls | tools | tokens | elapsed)
```

### Agent Status Tracking

```
pending → in_progress → completed
```

Transitions driven by streaming graph chunks: each chunk is inspected for report keys, debate state updates, and message content.

---

## 15. Checkpoint / Resume

### Implementation

Uses `langgraph-checkpoint-sqlite` to persist LangGraph state after each node.

```python
# Per-ticker SQLite DB:
{data_cache_dir}/checkpoints/{TICKER}.db

# Thread ID (deterministic):
thread_id = SHA256("{TICKER}:{DATE}")[:16]
```

### Flow

```
config["checkpoint_enabled"] = True
    │
    ▼
get_checkpointer(data_dir, ticker) as checkpointer
    │
    ▼
graph.compile(checkpointer=checkpointer)
    │
    ▼
graph.invoke(state, config={"thread_id": thread_id})
    │
    ├── Crash mid-run?
    │     → Same ticker + date → same thread_id → resume from last node
    │
    └── Success?
          → clear_checkpoint(data_dir, ticker, date)
```

---

## 16. Error Handling & Fallbacks

| Scenario | Handling |
|---|---|
| All data vendors fail | `RuntimeError` with vendor chain details |
| Alpha Vantage rate limit | Caught specifically; triggers yfinance fallback |
| StockTwits / Reddit unavailable | Returns placeholder string (`<unavailable>`) |
| yfinance empty data | Returns empty CSV with header notice |
| Structured output fails | `invoke_structured_or_freetext` retries as free text |
| Provider doesn't support tool_choice | `capabilities.py` suppresses the kwarg |
| DeepSeek reasoning roundtrip | `requires_reasoning_content_roundtrip=True` echoes reasoning block |
| Missing API key | `ensure_api_key()` prompts user to paste and saves to `.env` |
| Future analysis date | CLI validation rejects; raw API check in `get_analysis_date()` |
| Returns unavailable for reflection | `_fetch_returns()` returns `(None, None, None)`; reflection skipped |
| Checkpoint resume | LangGraph automatic via `thread_id` determinism |

---

## 17. End-to-End Execution Flow

```
1. TradingAgentsGraph.__init__()
   ├── create_llm_client(quick)  →  quick_llm
   ├── create_llm_client(deep)   →  deep_llm
   ├── set_config(config)        →  dataflow vendor routing
   ├── ConditionalLogic(config)  →  flow control lambdas
   ├── GraphSetup(...)           →  builds LangGraph
   ├── Propagator(...)           →  state factory
   ├── Reflector(quick_llm)      →  reflection generator
   └── SignalProcessor()         →  rating extractor

2. propagate(ticker, date)
   ├── _resolve_pending_entries(ticker)
   │   └── For each pending entry: fetch returns → reflect → update log
   └── _run_graph(ticker, date)

3. _run_graph(ticker, date)
   ├── get_past_context(ticker)  →  past_context string
   ├── create_initial_state()    →  AgentState dict
   ├── get_graph_args()          →  {stream_mode, config, recursion_limit}
   └── graph.stream(state, **args) → iterate chunks

4. Analyst Phase (per selected analyst):
   analyst_node invoked
   └── LLM.bind_tools(tools).invoke(messages)
       ├── Tool calls present → ToolNode → route_to_vendor → yfinance/AV
       │   └── Loop back to analyst_node with tool results
       └── No tool calls → report extracted from messages → messages cleared

5. Investment Debate Phase:
   Bull Researcher invoked
   └── LLM.invoke(4 reports + debate history) → argument
   Bear Researcher invoked
   └── LLM.invoke(4 reports + debate history) → counter-argument
   [Repeat up to 2 * max_debate_rounds]
   Research Manager invoked
   └── invoke_structured_or_freetext → ResearchPlan → investment_plan

6. Trading Phase:
   Trader invoked
   └── invoke_structured_or_freetext → TraderProposal → trader_investment_plan

7. Risk Debate Phase:
   Aggressive / Conservative / Neutral cycle
   [Repeat up to 3 * max_risk_discuss_rounds]
   Portfolio Manager invoked
   └── invoke_structured_or_freetext → PortfolioDecision → final_trade_decision

8. Post-processing:
   ├── process_signal(final_trade_decision) → "Buy" | "Overweight" | ... | "Sell"
   ├── _log_state(date, final_state) → JSON file on disk
   ├── memory_log.store_decision(ticker, date, final_trade_decision)
   └── clear_checkpoint() if enabled

9. (Next run, same ticker)
   └── _resolve_pending_entries() → fetch real returns → reflect → update log
```

---

## 18. Key Design Decisions

| Decision | Rationale |
|---|---|
| **Adversarial debate** instead of single-LLM analysis | Prevents groupthink; forces explicit counterarguments; improves decision quality |
| **5-tier rating** (not binary buy/sell) | Granular position sizing (overweight ≠ full buy); mirrors real portfolio management |
| **Serial analyst execution** (concurrency_limit=1) | Avoids message ordering bugs in LangGraph state; simpler debugging |
| **Sentiment pre-fetch** (no tool loop) | StockTwits/Reddit have no structured query API; all data retrieved upfront and injected as context |
| **Message clearing** after each analyst | Prevents Anthropic context length errors from accumulating tool result messages |
| **Structured output with free-text fallback** | Works with all providers including Ollama local models that don't support JSON schema |
| **Deferred reflection** (Phase B on next run) | Cannot know outcome at decision time; 5-day holding window gives meaningful signal |
| **Per-ticker SQLite checkpoints** | Prevents concurrent ticker contention; enables partial resume of long runs |
| **Vendor routing layer** | Swap yfinance ↔ Alpha Vantage without touching agent code; transparent fallback on rate limits |
| **TRADINGAGENTS_* env overrides** | Run in CI/Docker without modifying code; supports multiple config profiles |
| **Lazy LLM client imports** | Tests collect without needing all API SDKs installed |
| **normalize_content()** | Handles divergent response formats across providers (OpenAI Responses API list blocks, Gemini 3.x, etc.) |
| **Benchmark auto-detection** via suffix | Non-US tickers (.T, .HK, .NS) get regional benchmarks automatically; no manual config needed |

---

## Quick Recreation Checklist

To build a replica from scratch:

- [ ] Set up LangGraph `StateGraph` with `MessagesState` subclass
- [ ] Implement `AgentState`, `InvestDebateState`, `RiskDebateState` TypedDicts
- [ ] Build 4 analyst node functions (market, sentiment, news, fundamentals)
- [ ] Implement tool loop: `bind_tools` → conditional edge → `ToolNode` → back to agent
- [ ] Add message clear node (Anthropic context management)
- [ ] Build bull/bear researcher nodes with debate state accumulation
- [ ] Implement debate loop: conditional edge routing on count threshold
- [ ] Build Research Manager with structured output + fallback
- [ ] Build Trader with structured output + fallback
- [ ] Build 3 risk debater nodes with risk_debate_state accumulation
- [ ] Build Portfolio Manager with structured output + fallback
- [ ] Implement `parse_rating()` for deterministic 5-tier extraction
- [ ] Implement vendor routing (`route_to_vendor`) with fallback chain
- [ ] Wire yfinance data functions for price, indicators, fundamentals, news
- [ ] Scrape StockTwits and Reddit public APIs (no auth required)
- [ ] Implement `TradingMemoryLog` with Phase A/B write/resolve
- [ ] Implement `Reflector` for deferred outcome reflection
- [ ] Build `create_llm_client()` factory for at least 2 providers
- [ ] Implement `invoke_structured_or_freetext()` structured output helper
- [ ] Build CLI with `typer` + `questionary` + `rich` Live display
- [ ] Add `TRADINGAGENTS_*` env var override system
- [ ] Add SQLite checkpoint support (optional)
