# TradingAgents — Complete Codebase Reference

Every file, every function, every parameter, every return value.

---

## Table of Contents

1. [Entry Points](#1-entry-points)
2. [tradingagents/default_config.py](#2-tradingagentsdefault_configpy)
3. [agents/utils — Shared Utilities](#3-agentsutils--shared-utilities)
4. [agents/analysts — Analyst Nodes](#4-agentsanalysts--analyst-nodes)
5. [agents/researchers — Debate Layer](#5-agentsresearchers--debate-layer)
6. [agents/managers — Judge Layer](#6-agentsmanagers--judge-layer)
7. [agents/trader — Execution Layer](#7-agentstrader--execution-layer)
8. [agents/risk_mgmt — Risk Debate Layer](#8-agentsrisk_mgmt--risk-debate-layer)
9. [dataflows/config.py](#9-dataflowsconfigpy)
10. [dataflows/utils.py](#10-dataflowsutilspy)
11. [dataflows/interface.py](#11-dataflowsinterfacepy)
12. [dataflows — Stock Vendors](#12-dataflows--stock-vendors)
13. [dataflows — News Vendors](#13-dataflows--news-vendors)
14. [dataflows — Sentiment Vendors](#14-dataflows--sentiment-vendors)
15. [dataflows — Mutual Fund Vendors](#15-dataflows--mutual-fund-vendors)
16. [graph — Orchestration Layer](#16-graph--orchestration-layer)
17. [llm_clients — Provider Abstraction](#17-llm_clients--provider-abstraction)

---

## 1. Entry Points

---

### `main.py`

Top-level entry point. Decides between interactive TUI and Typer CLI based on whether arguments are passed.

#### `analyse(ticker, trade_date, provider, deep_model, quick_model, asset_type, invest_rounds, risk_rounds, json_out)`

**Type:** Typer CLI command (`@app.command()`)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | `str` | required | Ticker symbol or MFApi scheme code |
| `trade_date` | `str` | required | Analysis date in `YYYY-MM-DD` |
| `provider` | `str` | `"openai"` | LLM provider name |
| `deep_model` | `str` | `"gpt-4o"` | Model for heavy-reasoning agents |
| `quick_model` | `str` | `"gpt-4o-mini"` | Model for lightweight agents |
| `asset_type` | `str` | `"stock"` | `"stock"` or `"mutual_fund"` |
| `invest_rounds` | `int` | `1` | Number of investment debate rounds |
| `risk_rounds` | `int` | `1` | Number of risk debate rounds |
| `json_out` | `bool` | `False` | Dump raw signal dict as JSON |

**Returns:** Nothing (prints to console, exits with code 1 on error).

**What it does:** Builds a config dict from CLI options, calls `graph_run()`, then prints a Rich-styled result panel. If `--json`, dumps the full signal dict as JSON instead.

---

#### `main()`

**Returns:** Nothing.

**What it does:** Inspects `sys.argv`. If no arguments (bare `python main.py`), imports and calls `run_app.interactive()` for the TUI. Otherwise passes control to Typer's CLI parser which routes to `analyse()`.

---

### `run_app.py`

Interactive TUI built with `questionary` (prompts) and `rich` (display).

#### `_ask_provider() → str`

Presents a `questionary.select` dropdown of all available LLM providers. Returns the selected provider string (e.g. `"openai"`).

---

#### `_ask_model(provider: str) → tuple[str, str]`

| Parameter | Type | Description |
|---|---|---|
| `provider` | `str` | The selected provider |

**Returns:** `(deep_model, quick_model)` — two model name strings.

**What it does:** Fetches the model list for the provider. If the list is empty (open-catalog providers like Ollama and OpenRouter), prompts the user to type model names manually. Otherwise shows a select dropdown for deep-think model and another for quick-think model (with a `"same as deep"` shortcut).

---

#### `_ask_asset() → str`

Presents a select dropdown for asset type. Returns `"stock"` or `"mutual_fund"`.

---

#### `_ask_ticker(asset_type: str) → str`

| Parameter | Type | Description |
|---|---|---|
| `asset_type` | `str` | `"stock"` or `"mutual_fund"` |

**Returns:** The ticker symbol or MFApi scheme code as a string.

**What it does:** For mutual funds, shows a tip about finding scheme codes and prompts for a numeric scheme code. For stocks, shows example tickers and prompts, then uppercases the result.

---

#### `_ask_date() → str`

Prompts for analysis date in `YYYY-MM-DD` format, defaulting to today. Returns the date string.

---

#### `_ask_rounds() → tuple[int, int]`

Prompts for investment debate rounds (1–3) and risk debate rounds (1–3) via select dropdowns.

**Returns:** `(invest_rounds, risk_rounds)` as integers.

---

#### `_print_report_section(title: str, content: str) → None`

| Parameter | Description |
|---|---|
| `title` | Section heading to display |
| `content` | The markdown content to print |

**What it does:** Skips silently if `content` is empty or starts with `"N/A"`. Otherwise prints a Rich `Rule` separator with the title, then the content stripped of leading/trailing whitespace.

---

#### `_display_results(signal: dict) → None`

| Parameter | Description |
|---|---|
| `signal` | The signal dict returned by `graph_run()` |

**What it does:** Builds a Rich `Text` header with ticker, date, and colour-coded rating. Prints a bordered `Panel`. Then calls `_print_report_section` for each output section in order: final decision (as its own blue panel), investment plan, trader proposal, bull research, bear research, market report, fundamentals report, news report, sentiment report, holdings report, category report.

---

#### `interactive() → None`

**What it does:** The main TUI flow. Prints the TradingAgents welcome panel, then runs all `_ask_*` prompts in sequence. Builds the config dict. Calls `graph_run()` inside a Rich spinner. On completion calls `_display_results()` and `save_report()`, then prints the report file path. Handles `KeyboardInterrupt` and generic exceptions gracefully.

---

## 2. `tradingagents/default_config.py`

Defines the master configuration dictionary and override mechanisms.

#### `_apply_env_overrides(config: dict) → dict`

| Parameter | Description |
|---|---|
| `config` | A copy of DEFAULT_CONFIG |

**Returns:** The same dict with any `TRADINGAGENTS_<KEY>` environment variables applied.

**What it does:** Iterates every key in the config. For each key, checks for an env var named `TRADINGAGENTS_<KEY_UPPERCASE>`. If found, casts the value to the correct Python type (bool, int, float, or str) based on the original value's type, then overwrites the config key.

---

#### `get_config(overrides: dict | None = None) → dict`

| Parameter | Description |
|---|---|
| `overrides` | Optional caller-supplied dict to merge on top of the base config |

**Returns:** A fully resolved config dict.

**What it does:** Starts with a shallow copy of `DEFAULT_CONFIG`, applies env var overrides via `_apply_env_overrides()`, then applies any caller-supplied `overrides` using `dict.update()`. This is the single source of truth for config throughout the pipeline.

---

## 3. `agents/utils` — Shared Utilities

---

### `agents/utils/agent_states.py`

Defines the TypedDict schemas for all shared state objects.

#### `InvestDebateState` (TypedDict)

| Field | Type | Description |
|---|---|---|
| `bull_history` | `str` | Bull's cumulative arguments across all rounds |
| `bear_history` | `str` | Bear's cumulative arguments across all rounds |
| `history` | `str` | Combined chronological transcript of all turns |
| `current_response` | `str` | The latest speaker's message (used by routers) |
| `judge_decision` | `str` | Research Manager's final verdict markdown |
| `count` | `int` | Turn counter; incremented by 1 each time bull or bear speaks |

---

#### `RiskDebateState` (TypedDict)

| Field | Type | Description |
|---|---|---|
| `aggressive_history` | `str` | Aggressive debator's cumulative arguments |
| `conservative_history` | `str` | Conservative debator's cumulative arguments |
| `neutral_history` | `str` | Neutral debator's cumulative arguments |
| `history` | `str` | Combined transcript of all three speakers |
| `latest_speaker` | `str` | `"Aggressive"`, `"Conservative"`, or `"Neutral"` (used by router) |
| `current_aggressive_response` | `str` | Latest aggressive turn |
| `current_conservative_response` | `str` | Latest conservative turn |
| `current_neutral_response` | `str` | Latest neutral turn |
| `judge_decision` | `str` | Portfolio Manager's final verdict markdown |
| `count` | `int` | Turn counter; incremented by 1 each time any speaker speaks |

---

#### `AgentState` (extends `MessagesState`)

The master state dict flowing through the entire LangGraph pipeline.

| Field | Type | Description |
|---|---|---|
| `company_of_interest` | `str` | Ticker symbol or MFApi scheme code |
| `asset_type` | `str` | `"stock"` or `"mutual_fund"` |
| `trade_date` | `str` | `"YYYY-MM-DD"` |
| `sender` | `str` | Name of the last agent that wrote to state |
| `market_report` | `str` | Output of market_analyst |
| `sentiment_report` | `str` | Output of sentiment_analyst |
| `news_report` | `str` | Output of news_analyst |
| `fundamentals_report` | `str` | Output of fundamentals_analyst |
| `holdings_report` | `str` | Output of holdings_analyst (MFs) |
| `category_report` | `str` | Output of category_analyst (MFs) |
| `fund_benchmark` | `str` | Fund's declared benchmark ticker (e.g. `"^NSEI"`) |
| `investment_debate_state` | `InvestDebateState` | Full bull/bear debate state |
| `investment_plan` | `str` | Research Manager's final plan markdown |
| `trader_investment_plan` | `str` | Trader's proposal markdown |
| `risk_debate_state` | `RiskDebateState` | Full three-way risk debate state |
| `final_trade_decision` | `str` | Portfolio Manager's final decision markdown |
| `past_context` | `str` | Prior decisions injected from memory at run start |

---

### `agents/utils/agent_utils.py`

Core tool-calling loop and fallback mechanism used by every analyst.

#### `_prefetch_all_tools(tools: list, state: dict) → str`

| Parameter | Description |
|---|---|
| `tools` | List of LangChain `@tool`-decorated functions |
| `state` | The current `AgentState` dict |

**Returns:** A formatted plain-text string with one `[tool_name]\n<result>` block per tool, joined by double newlines. Returns `"No pre-fetched data available."` if all tools fail.

**What it does:** Used as a fallback when the LLM provider cannot generate valid tool calls (e.g. Groq/LLaMA malformed function-call XML). Derives arguments from state using a fixed `_ARG_MAP` that maps common parameter names (`ticker`, `symbol`, `scheme_code`, `query`, `start_date`, `end_date`, `curr_date`, `freq`, `benchmark_code`, `look_back_days`, `limit`) to values extracted from state. For each tool, inspects its Pydantic `args_schema.model_fields` to determine which params to pass, calls `tool.invoke(kwargs)`, and collects results.

---

#### `_flatten_content(content) → str`

| Parameter | Description |
|---|---|
| `content` | LLM response content (str or list of typed blocks) |

**Returns:** A plain string.

**What it does:** If `content` is a list (as returned by some providers like Gemini or OpenAI Responses API), extracts the `"text"` key from each dict block and joins with newlines. Otherwise returns `str(content)`.

---

#### `run_agent_node(state, llm, tools, system_prompt, output_key) → dict`

| Parameter | Type | Description |
|---|---|---|
| `state` | `dict` | Current `AgentState` |
| `llm` | `BaseChatModel` | The LangChain LLM (already unwrapped via `.get_llm()`) |
| `tools` | `list` | List of `@tool` functions to make available |
| `system_prompt` | `str` | The agent's role/instructions |
| `output_key` | `str` | Which AgentState key to write the result into |

**Returns:** `{output_key: final_text_response}` — a partial state dict.

**What it does:** Implements the standard LangChain tool-calling loop:
1. Binds tools to the LLM via `llm.bind_tools(tools)`
2. Builds the initial messages: `SystemMessage(system_prompt)` + `HumanMessage(ticker | type | date | past_context)`
3. **Primary loop**: Calls `llm_with_tools.invoke(messages)`. If the response has `tool_calls`, executes each tool via `tool_map[name].invoke(args)`, appends a `ToolMessage`, and loops. Exits when response has no tool calls.
4. **Fallback**: If the primary loop raises any exception, calls `_prefetch_all_tools()` to eagerly fetch all data, injects it as plain text into a new `HumanMessage`, and calls the plain (non-tool-bound) LLM once.
5. Returns `{output_key: _flatten_content(response.content)}`.

---

### `agents/utils/schemas.py`

Pydantic v2 models used for structured LLM output in managers and the trader.

#### `PortfolioRating` (str Enum)

Values: `"Buy"`, `"Overweight"`, `"Hold"`, `"Underweight"`, `"Sell"`

---

#### `TraderAction` (str Enum)

Values: `"Buy"`, `"Hold"`, `"Sell"`

---

#### `ResearchPlan` (BaseModel)

| Field | Type | Description |
|---|---|---|
| `recommendation` | `PortfolioRating` | The research manager's rating |
| `rationale` | `str` | Evidence-based justification from the debate |
| `strategic_actions` | `str` | Specific price levels, catalysts, or exit conditions |

---

#### `TraderProposal` (BaseModel)

| Field | Type | Description |
|---|---|---|
| `action` | `TraderAction` | Buy / Hold / Sell |
| `reasoning` | `str` | Why this action given the research plan |
| `entry_price` | `Optional[float]` | Suggested entry price |
| `stop_loss` | `Optional[float]` | Stop loss level |
| `position_sizing` | `Optional[str]` | e.g. `"5% of portfolio"` |

---

#### `PortfolioDecision` (BaseModel)

| Field | Type | Description |
|---|---|---|
| `rating` | `PortfolioRating` | Final 5-tier rating |
| `executive_summary` | `str` | 2–3 sentence plain-English summary |
| `investment_thesis` | `str` | The core bull or bear case that won |
| `price_target` | `Optional[float]` | 12-month price or NAV target |
| `risk_factors` | `Optional[str]` | Key risks that could invalidate the thesis |
| `time_horizon` | `Optional[str]` | e.g. `"6–12 months"` |

---

### `agents/utils/structured.py`

Helpers for structured output with automatic free-text fallback.

#### `bind_structured(llm, schema) → BaseChatModel`

| Parameter | Type | Description |
|---|---|---|
| `llm` | `BaseChatModel` | The unwrapped LangChain model |
| `schema` | `type[T]` | A Pydantic BaseModel subclass |

**Returns:** `llm.with_structured_output(schema)` — the LLM bound to produce validated Pydantic instances.

---

#### `invoke_structured_or_freetext(structured_llm, plain_llm, prompt, render, agent_name) → str`

| Parameter | Type | Description |
|---|---|---|
| `structured_llm` | `BaseChatModel` | LLM bound with `with_structured_output` |
| `plain_llm` | `BaseChatModel` | Same LLM without structured binding |
| `prompt` | `list` | Messages list (SystemMessage + HumanMessage) |
| `render` | `Callable[[T], str]` | Converts the Pydantic instance to a markdown string |
| `agent_name` | `str` | Used only for warning log messages |

**Returns:** A markdown string — either rendered from the Pydantic instance (success path) or the raw LLM text response (fallback path).

**What it does:** Tries `structured_llm.invoke(prompt)`. If it succeeds, calls `render(result)` and returns the markdown. If it raises any exception (provider doesn't support structured output, schema mismatch, etc.), logs a warning and falls back to `plain_llm.invoke(prompt)`, flattening list-of-blocks content to plain text before returning.

---

### `agents/utils/rating.py`

Rating extraction from free-form LLM text.

#### `parse_rating(text: str, default: str = "Hold") → str`

| Parameter | Type | Description |
|---|---|---|
| `text` | `str` | Any LLM-generated prose or markdown |
| `default` | `str` | Returned if no rating found (default `"Hold"`) |

**Returns:** One of `"Buy"`, `"Overweight"`, `"Hold"`, `"Underweight"`, `"Sell"`.

**What it does:**
- **Pass 1**: Searches for an explicit `"Rating: X"` or `"Recommendation: X"` label using `_LABEL_RE` regex, tolerant of surrounding markdown bold (`**`).
- **Pass 2**: Also tries `_BOLD_RE` which catches `**Rating: Buy**` patterns.
- **Pass 3**: Searches the entire text for the first occurrence of any rating word as a whole word (`\b` boundary).
- **Pass 4**: Returns `default` if nothing matched.

---

### `agents/utils/core_stock_tools.py`

#### `get_stock_data_tool(symbol, start_date, end_date) → str`  *(LangChain @tool)*

| Parameter | Description |
|---|---|
| `symbol` | Ticker symbol (e.g. `"RELIANCE.NS"`) |
| `start_date` | `"YYYY-MM-DD"` |
| `end_date` | `"YYYY-MM-DD"` |

**Returns:** CSV string with columns Open, High, Low, Close, Volume.

**What it does:** Calls `route_to_vendor("get_stock_data", symbol, start_date, end_date)`. Routes to yfinance by default, with alpha_vantage as fallback.

---

### `agents/utils/technical_indicators_tools.py`

#### `get_technical_indicators_tool(symbol, indicator, curr_date, look_back_days=30) → str`  *(LangChain @tool)*

| Parameter | Description |
|---|---|
| `symbol` | Ticker symbol |
| `indicator` | Indicator name or comma-separated list (e.g. `"rsi_14,macd,boll"`) |
| `curr_date` | `"YYYY-MM-DD"` — the as-of date |
| `look_back_days` | How many days of indicator history to return (default 30) |

**Returns:** Formatted string with date-indexed indicator values.

**What it does:** Calls `route_to_vendor("get_indicators", ...)`. Routes to `stockstats_utils.get_indicators()`.

---

### `agents/utils/fundamental_data_tools.py`

#### `get_fundamentals_tool(ticker, curr_date) → str`  *(LangChain @tool)*

Fetches PE, PB, EV/EBITDA, margins, ROE, debt/equity, dividend yield, analyst target, 52-week range, beta. Routes to `route_to_vendor("get_fundamentals", ticker, curr_date)`.

---

#### `get_balance_sheet_tool(ticker, freq="quarterly", curr_date="") → str`  *(LangChain @tool)*

Fetches the balance sheet. `freq` must be `"quarterly"` or `"annual"`. Routes to `route_to_vendor("get_balance_sheet", ...)`.

---

#### `get_cashflow_tool(ticker, freq="quarterly", curr_date="") → str`  *(LangChain @tool)*

Fetches the cash flow statement (operating / investing / financing). Routes to `route_to_vendor("get_cashflow", ...)`.

---

#### `get_income_statement_tool(ticker, freq="quarterly", curr_date="") → str`  *(LangChain @tool)*

Fetches the income statement (revenue, gross profit, EBITDA, operating income, net income). Routes to `route_to_vendor("get_income_statement", ...)`.

---

### `agents/utils/news_data_tools.py`

#### `get_news_tool(ticker, start_date, end_date) → str`  *(LangChain @tool)*

Fetches recent news articles for a ticker between two dates. Routes to `route_to_vendor("get_news", ...)`. Primary vendor: Tavily, fallback chain: rss_news → newsapi → finnhub → yfinance → alpha_vantage.

---

#### `get_global_news_tool(curr_date, look_back_days=7, limit=10) → str`  *(LangChain @tool)*

Fetches global macro and financial market news. Routes to `route_to_vendor("get_global_news", ...)`. Same vendor fallback chain as `get_news`.

---

#### `get_reddit_sentiment_tool(ticker, limit=25) → str`  *(LangChain @tool)*

Fetches Reddit posts mentioning the ticker from r/wallstreetbets, r/investing, r/stocks, sorted by score. Routes directly to the `reddit` vendor via `tool_vendors` config.

---

### `agents/utils/sentiment_data_tools.py`

#### `get_stocktwits_sentiment_tool(ticker, limit=30) → str`  *(LangChain @tool)*

Fetches recent StockTwits messages with Bullish / Bearish / Neutral labels. Routes directly to the `stocktwits` vendor.

---

#### `get_google_trends_tool(ticker, look_back_days=30) → str`  *(LangChain @tool)*

Gets Google Search interest trend (0–100 scale) for the ticker over the past N days. Rising search interest often precedes increased retail attention and volatility. Routes directly to the `google_trends` vendor.

---

#### `get_fear_greed_tool(curr_date) → str`  *(LangChain @tool)*

Fetches the CNN Money Fear & Greed Index (stock market) and the Alternative.me index (crypto, as corroborating signal). Score 0=Extreme Fear, 50=Neutral, 100=Extreme Greed. Routes directly to the `fear_greed` vendor.

---

### `agents/utils/fund_tools.py`

#### `get_fund_nav_history_tool(scheme_code, start_date, end_date) → str`  *(LangChain @tool)*

Fetches historical NAV for an Indian mutual fund. `scheme_code` is the numeric MFApi scheme code. Returns a CSV of `Date,NAV`. Routes to `route_to_vendor("get_fund_nav_history", ...)`.

---

#### `get_fund_info_tool(scheme_code) → str`  *(LangChain @tool)*

Fetches fund metadata: scheme name, fund house (AMC), scheme type, scheme category, latest NAV and NAV date. Routes to `route_to_vendor("get_fund_info", ...)`.

---

#### `get_trailing_returns_tool(scheme_code, benchmark_code="^NSEI") → str`  *(LangChain @tool)*

Calculates trailing returns over 1M / 3M / 6M / 1Y / 3Y / 5Y vs a benchmark index. `benchmark_code` is a yfinance ticker (default `"^NSEI"` for Nifty 50). Routes to `route_to_vendor("get_trailing_returns", ...)`.

---

#### `search_fund_tool(query) → str`  *(LangChain @tool)*

Searches Indian mutual funds by partial name. Returns a list of matching scheme codes and names. Routes to `route_to_vendor("search_fund", ...)`.

---

#### `get_fund_by_category_tool(category) → str`  *(LangChain @tool)*

Lists all Indian mutual fund schemes in a given SEBI category (e.g. `"Large Cap Fund"`, `"ELSS"`, `"Liquid Fund"`). Routes to `route_to_vendor("get_category_funds", ...)`.

---

## 4. `agents/analysts` — Analyst Nodes

Each analyst file defines a `create_X_analyst(llm, config)` factory that returns a LangGraph node function. All analysts call `run_agent_node()` internally.

---

### `agents/analysts/market_analyst.py`

#### `create_market_analyst(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**Tools used:** `get_stock_data_tool`, `get_technical_indicators_tool`

**Output key:** `"market_report"`

**What the node does:** Fetches 60 days of OHLCV data. Calculates RSI-14, MACD, Bollinger Bands, 20/50-day SMA, ATR. Identifies primary trend (uptrend / downtrend / sideways), key support/resistance levels, and momentum signals. Returns structured markdown with a preliminary rating.

---

### `agents/analysts/fundamentals_analyst.py`

#### `create_fundamentals_analyst(llm, config) → Callable`

**Returns:** A node function.

**Tools used:** `get_fundamentals_tool`, `get_balance_sheet_tool`, `get_cashflow_tool`, `get_income_statement_tool`

**Output key:** `"fundamentals_report"`

**What the node does:** Fetches the full company overview (valuation ratios, margins, ROE, debt/equity). Reviews the last two quarters of the balance sheet, cash flow statement (free cash flow focus), and income statement (revenue growth, margin trend). Assesses whether the stock is fairly valued vs sector norms. Returns markdown with a preliminary rating.

---

### `agents/analysts/news_analyst.py`

#### `create_news_analyst(llm, config) → Callable`

**Returns:** A node function.

**Tools used:** `get_news_tool`, `get_global_news_tool`

**Output key:** `"news_report"`

**What the node does:** Fetches company-specific news (14-day lookback) and global macro news. Identifies catalysts (earnings, product launches, management changes) and headwinds (regulatory, geopolitical, rate signals). Classifies overall news sentiment as Bullish / Neutral / Bearish. Returns a table of headlines plus summary sections.

---

### `agents/analysts/sentiment_analyst.py`

#### `create_sentiment_analyst(llm, config) → Callable`

**Returns:** A node function.

**Tools used:** `get_reddit_sentiment_tool`, `get_stocktwits_sentiment_tool`, `get_google_trends_tool`, `get_fear_greed_tool`

**Output key:** `"sentiment_report"`

**What the node does:** Fetches Reddit posts (sorted by upvote score), StockTwits messages (Bullish/Bearish labels), Google Search trend data, and the Fear & Greed Index. Synthesises overall retail mood, flags meme-stock dynamics, short-squeeze talk, and options speculation. Notes whether retail sentiment diverges from fundamentals. Assigns a retail sentiment score (Strong Buy through Strong Sell).

---

### `agents/analysts/holdings_analyst.py`

#### `create_holdings_analyst(llm, config) → Callable`

**Returns:** A node function.

**Tools used:** `get_fund_nav_history_tool`, `get_fund_info_tool`, `get_trailing_returns_tool`

**Output key:** `"holdings_report"`

**Guard:** If `state["asset_type"] != "mutual_fund"`, immediately returns `{"holdings_report": "N/A — asset is not a mutual fund."}` without calling the LLM.

**What the node does:** Fetches fund metadata (name, AMC, category, type), 1-year NAV history (trend analysis), and trailing returns across 1M / 3M / 6M / 1Y / 3Y / 5Y vs the declared benchmark. Assesses consistent outperformance or underperformance, notable drawdowns, and recovery patterns. Returns markdown with a preliminary rating.

---

### `agents/analysts/category_analyst.py`

#### `create_category_analyst(llm, config) → Callable`

**Returns:** A node function.

**Tools used:** `get_fund_by_category_tool`, `search_fund_tool`

**Output key:** `"category_report"`

**Guard:** If `state["asset_type"] != "mutual_fund"`, returns `{"category_report": "N/A — asset is not a mutual fund."}`.

**What the node does:** Confirms the fund's SEBI category, lists all peer funds in that category, looks up 2–3 top-performing peers by name for comparison, assesses the fund's relative positioning (AUM, strategy), and rates the category itself given macro conditions. Returns markdown with a preliminary rating.

---

## 5. `agents/researchers` — Debate Layer

---

### `agents/researchers/bull_researcher.py`

#### `_build_reports_block(state: AgentState) → str`

| Parameter | Description |
|---|---|
| `state` | Current `AgentState` |

**Returns:** A multi-section string with labelled analyst reports (skips empty or N/A-sentinel reports).

**What it does:** Iterates through six state keys (`market_report`, `fundamentals_report`, `news_report`, `sentiment_report`, `holdings_report`, `category_report`), formats each as `=== LABEL ===\n<content>`, and joins with double newlines.

---

#### `create_bull_researcher(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**What the node does:**
1. Reads `investment_debate_state` from state to get bear's previous arguments and current round count.
2. Calls `_build_reports_block(state)` to get all analyst data.
3. Builds a HumanMessage: ticker + analyst reports + (if bear has spoken) bear's prior arguments with instruction to counter them.
4. Invokes the LLM with the system prompt (arguing FOR the investment).
5. Appends the new content to `bull_history`, appends to the combined `history` transcript with a round label, increments `count` by 1.
6. Returns partial state updating `investment_debate_state`.

---

### `agents/researchers/bear_researcher.py`

#### `_build_reports_block(state: AgentState) → str`

Identical to the one in `bull_researcher.py`. Formats all analyst reports for injection into the bear's prompt.

---

#### `create_bear_researcher(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**What the node does:** Mirror of `create_bull_researcher` but argues AGAINST the investment. Reads bull's prior arguments, counters them point by point. Appends to `bear_history` and combined `history`, increments `count` by 1. Returns partial state updating `investment_debate_state`.

---

## 6. `agents/managers` — Judge Layer

---

### `agents/managers/research_manager.py`

#### `_render_plan(plan: ResearchPlan) → str`

| Parameter | Description |
|---|---|
| `plan` | A validated `ResearchPlan` Pydantic instance |

**Returns:** Markdown string with heading, rating, rationale, and strategic actions.

---

#### `create_research_manager(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**What the node does:**
1. Reads the full `investment_debate_state.history` (combined bull/bear transcript).
2. Calls `invoke_structured_or_freetext()` with the `ResearchPlan` schema:
   - **Primary**: Gets a structured `ResearchPlan` instance (rating + rationale + strategic_actions), renders it to markdown via `_render_plan()`.
   - **Fallback**: Gets free-text markdown if structured output fails.
3. Writes `investment_plan` to state and also stores it in `investment_debate_state.judge_decision`.

---

### `agents/managers/portfolio_manager.py`

#### `_render_decision(decision: PortfolioDecision) → str`

| Parameter | Description |
|---|---|
| `decision` | A validated `PortfolioDecision` Pydantic instance |

**Returns:** Full markdown decision with rating, executive summary, investment thesis, price target, time horizon, and risk factors.

---

#### `create_portfolio_manager(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**What the node does:**
1. Reads `investment_plan`, `trader_investment_plan`, and `risk_debate_state.history` from state.
2. Presents all three to the LLM as the final context.
3. Calls `invoke_structured_or_freetext()` with the `PortfolioDecision` schema.
4. Returns `final_trade_decision` (the rendered markdown decision) and updates `risk_debate_state.judge_decision`.

---

## 7. `agents/trader` — Execution Layer

### `agents/trader/trader.py`

#### `_render_proposal(proposal: TraderProposal) → str`

| Parameter | Description |
|---|---|
| `proposal` | A validated `TraderProposal` Pydantic instance |

**Returns:** Markdown string with action, reasoning, entry price, stop loss, and position sizing (skips None fields).

---

#### `create_trader(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**What the node does:**
1. Reads `investment_plan`, `company_of_interest`, `trade_date`, `asset_type` from state.
2. Calls `invoke_structured_or_freetext()` with the `TraderProposal` schema:
   - **Primary**: Gets a structured `TraderProposal` (action, reasoning, entry price, stop loss, position sizing), renders to markdown via `_render_proposal()`.
   - **Fallback**: Gets free-text proposal if structured output fails.
3. Returns `{"trader_investment_plan": rendered_proposal}`.

---

## 8. `agents/risk_mgmt` — Risk Debate Layer

---

### `agents/risk_mgmt/aggressive_debator.py`

#### `create_aggressive_debator(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**Philosophy:** Markets reward decisive action. Missed opportunity is the real risk.

**What the node does:**
1. Reads `risk_debate_state`, `trader_investment_plan`, and current debate history from state.
2. Builds a prompt: trader proposal + (if any) prior risk debate history.
3. Invokes LLM arguing for HIGHER exposure, LARGER position sizes, MORE aggressive entry.
4. Appends response to `aggressive_history` and combined `history` with round label `[Aggressive Round N]`.
5. Sets `latest_speaker = "Aggressive"`, increments `count` by 1.
6. Returns partial state updating `risk_debate_state`.

---

### `agents/risk_mgmt/conservative_debator.py`

#### `create_conservative_debator(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**Philosophy:** Capital preservation first. Focus on tail risks and downside scenarios.

**What the node does:** Mirror of `create_aggressive_debator` but argues for LOWER exposure, TIGHTER stop losses, MORE cautious entry. Appends to `conservative_history`, sets `latest_speaker = "Conservative"`, increments `count` by 1.

---

### `agents/risk_mgmt/neutral_debator.py`

#### `create_neutral_debator(llm, config) → Callable`

**Returns:** A node function `node(state: AgentState) → dict`.

**Philosophy:** Balance is not weakness. Synthesise aggressive and conservative into an executable middle ground.

**What the node does:** Reads both sides' prior arguments, identifies the strongest points from each, and proposes a balanced position size / entry / stop loss. Appends to `neutral_history`, sets `latest_speaker = "Neutral"`, increments `count` by 1.

---

## 9. `dataflows/config.py`

Module-level config store. Avoids threading issues by using a simple global (acceptable for single-threaded graph execution).

#### `set_config(config: dict) → None`

Replaces the module-level `_config` dict. Called once by `build_graph()` before the graph is compiled and invoked.

---

#### `get_config() → dict`

Returns the currently stored config dict. Called by conditional routers inside the LangGraph execution to read `max_debate_rounds` and `max_risk_discuss_rounds`.

---

## 10. `dataflows/utils.py`

Shared utility functions and exceptions used across vendor modules.

#### `AlphaVantageRateLimitError` (Exception subclass)

Custom exception raised when Alpha Vantage's rate limit is hit. The fallback chain in `interface.py` recognises this and tries the next vendor.

---

#### `safe_ticker_component(ticker: str) → str`

| Parameter | Description |
|---|---|
| `ticker` | Raw ticker string (e.g. `"RELIANCE.NS"`) |

**Returns:** Filename-safe version (e.g. `"RELIANCE_NS"`).

**What it does:** Replaces any non-word character (`[^\w]`) with `"_"` using regex.

---

#### `get_date_range(curr_date: str, look_back_days: int) → tuple[str, str]`

| Parameter | Description |
|---|---|
| `curr_date` | End date as `"YYYY-MM-DD"` |
| `look_back_days` | Number of calendar days to look back |

**Returns:** `(start_date, end_date)` both as `"YYYY-MM-DD"` strings. `end_date` is always `curr_date`.

---

#### `is_valid_date(date_str: str) → bool`

Returns `True` if `date_str` parses as `"%Y-%m-%d"`, `False` otherwise.

---

#### `format_number(value) → str`

| Parameter | Description |
|---|---|
| `value` | Any numeric value |

**Returns:** String with K / M / B suffix (e.g. `"1.23B"`, `"456.78M"`). Returns `str(value)` if not numeric.

---

## 11. `dataflows/interface.py`

The central vendor dispatch layer. All `@tool` functions call `route_to_vendor()`.

#### `_load_vendor_module(vendor: str)`

| Parameter | Description |
|---|---|
| `vendor` | Vendor name string (e.g. `"yfinance"`, `"tavily"`, `"mfapi"`) |

**Returns:** The imported vendor module object.

**What it does:** Lazy-imports the vendor module using a chain of `if vendor == "..."` checks. Raises `ValueError` for unknown vendor names. Supported vendors: `tavily`, `rss_news`, `newsapi`, `finnhub`, `yfinance`, `alpha_vantage`, `mfapi`, `amfi`, `reddit`, `stocktwits`, `google_trends`, `fear_greed`.

---

#### `route_to_vendor(method_name: str, *args, **kwargs)`

| Parameter | Description |
|---|---|
| `method_name` | The function name to call on the vendor module (e.g. `"get_news"`) |
| `*args` | Positional arguments forwarded to the vendor function |
| `**kwargs` | Keyword arguments forwarded to the vendor function |

**Returns:** Whatever the vendor function returns (typically a string).

**What it does (full resolution order):**
1. Initialises `all_vendors = _STOCK_VENDORS` (default fallback list for non-fund tools).
2. Checks `config["tool_vendors"][method_name]` — if found, uses that as the primary vendor directly (skips category lookup). This is used for single-vendor sentiment tools.
3. If no tool-level override: looks up `_TOOL_TO_CATEGORY[method_name]`. For `nav_data` / `fund_info` categories, uses `fund_data_vendors` config and `_FUND_VENDORS` list. For all other categories, uses `data_vendors` config and `_STOCK_VENDORS` list.
4. Builds `fallback_chain = [primary] + [v for v in all_vendors if v != primary]`.
5. Iterates the chain: lazy-imports each vendor via `_load_vendor_module()`, checks if the vendor implements `method_name` via `getattr()`, calls it if so. On any exception, records the error and tries the next vendor.
6. If all vendors are exhausted, raises `RuntimeError` with the full chain attempted and the last error.

---

## 12. `dataflows` — Stock Vendors

---

### `dataflows/y_finance.py`

Primary stock data vendor. Uses the `yfinance` library.

#### `get_stock_data(symbol, start_date, end_date) → str`

Downloads OHLCV price history via `yf.Ticker.history()`. Returns a CSV string with columns Open, High, Low, Close, Volume. Returns an error string if `symbol` is not found or the date range is empty.

---

#### `get_fundamentals(ticker, curr_date) → str`

Fetches `yf.Ticker.info` and extracts ~25 key fields: company name, sector, industry, market cap, enterprise value, trailing/forward PE, P/B, P/S, EV/EBITDA, ROE, ROA, profit/gross margin, debt/equity, current ratio, quick ratio, revenue (TTM), earnings (TTM), FCF, dividend yield, 52-week high/low, beta, analyst target. Formats numbers with K/M/B suffixes via `format_number()`.

---

#### `get_balance_sheet(ticker, freq="quarterly", curr_date=None) → str`

Fetches `yf.Ticker.quarterly_balance_sheet` (or `.balance_sheet` for annual). Returns a formatted string table. Truncates column headers to 10 characters to avoid wide output.

---

#### `get_cashflow(ticker, freq="quarterly", curr_date=None) → str`

Fetches `yf.Ticker.quarterly_cashflow` (or `.cashflow`). Returns a formatted string table.

---

#### `get_income_statement(ticker, freq="quarterly", curr_date=None) → str`

Fetches `yf.Ticker.quarterly_income_stmt` (or `.income_stmt`). Returns a formatted string table.

---

#### `_format_news_item(i, item) → str`  *(private)*

Formats a single yfinance news dict into a numbered line: `"N. [YYYY-MM-DD] Title — Publisher"`. Converts Unix timestamp to date string.

---

#### `get_news(ticker, start_date, end_date) → str`

Fetches `yf.Ticker.news`, filters to the given date range using `providerPublishTime` Unix timestamps. Falls back to all available news if the date filter returns nothing. Returns up to 20 formatted news items.

---

#### `get_global_news(curr_date, look_back_days=7, limit=10) → str`

Fetches news from three broad market proxy tickers: `^GSPC` (S&P 500), `^DJI` (Dow Jones), `^IXIC` (Nasdaq). Deduplicates by title, filters by date range, caps at `limit` articles.

---

#### `get_insider_transactions(ticker) → str`

Fetches `yf.Ticker.insider_transactions` DataFrame. Returns a formatted string table or an error message if no data is available.

---

### `dataflows/stockstats_utils.py`

Technical indicator calculation using the `stockstats` library on top of yfinance data.

**Module constant:** `SUPPORTED_INDICATORS` — tuple of all indicator names that stockstats can compute: `close_50_sma`, `close_200_sma`, `close_10_ema`, `macd`, `macds`, `macdh`, `rsi`, `boll`, `boll_ub`, `boll_lb`, `atr`, `vwma`, `mfi`.

---

#### `get_indicators(symbol, indicator, curr_date, look_back_days=30) → str`

| Parameter | Description |
|---|---|
| `symbol` | Ticker symbol |
| `indicator` | Single name or comma-separated list (e.g. `"rsi,macd,close_50_sma"`) |
| `curr_date` | As-of date `"YYYY-MM-DD"` |
| `look_back_days` | Days of indicator history to show (default 30) |

**Returns:** Formatted multi-section string with one `--- INDICATOR ---\n<date-indexed values>` block per indicator.

**What it does:**
1. Downloads `look_back_days + 250` calendar days of price data (extra days needed for SMA/MACD warmup).
2. Flattens any MultiIndex columns from newer yfinance versions, lowercases column names.
3. Wraps the DataFrame with `stockstats.wrap()` to enable indicator column syntax.
4. For each requested indicator, calls `stock[ind].dropna().tail(look_back_days)` and formats.
5. Returns all indicators joined with double newlines, or error messages for unsupported/unavailable indicators.

---

### `dataflows/alpha_vantage_stock.py`

Alpha Vantage fallback for stock and fundamental data. Requires `ALPHA_VANTAGE_API_KEY`.

#### `_check_rate_limit(data: dict) → None`  *(private)*

Raises `AlphaVantageRateLimitError` if the response dict contains the rate limit message `"Thank you for using Alpha Vantage"` in the `"Note"` or `"Information"` fields.

---

#### `get_stock_data(symbol, start_date, end_date) → str`

Fetches full daily adjusted OHLCV from Alpha Vantage `TIME_SERIES_DAILY_ADJUSTED`, filters to date range, renames columns, returns CSV. Re-raises `AlphaVantageRateLimitError` so the fallback chain can skip to the next vendor.

---

#### `get_fundamentals(ticker, curr_date) → str`

Fetches `OVERVIEW` endpoint from Alpha Vantage. Extracts ~20 fundamental fields. Re-raises rate limit errors.

---

#### `get_balance_sheet(ticker, freq="quarterly", curr_date=None) → str`

Fetches `BALANCE_SHEET` quarterly or annual from Alpha Vantage. Returns DataFrame string table.

---

#### `get_cashflow(ticker, freq="quarterly", curr_date=None) → str`

Fetches `CASH_FLOW` quarterly or annual from Alpha Vantage. Returns DataFrame string table.

---

#### `get_income_statement(ticker, freq="quarterly", curr_date=None) → str`

Fetches `INCOME_STATEMENT` quarterly or annual from Alpha Vantage. Returns DataFrame string table.

---

## 13. `dataflows` — News Vendors

---

### `dataflows/tavily.py`

Primary news vendor. Requires `TAVILY_API_KEY`.

**Module constant:** `_GLOBAL_QUERIES` — list of 5 macro search queries used for `get_global_news`.

#### `_client() → TavilyClient`  *(private)*

Lazy-imports `TavilyClient` from `tavily` package. Raises `RuntimeError` if `TAVILY_API_KEY` is not set.

---

#### `_date_to_days(start_date, end_date) → int`  *(private)*

Converts a date range to a lookback days integer (clamped to 1–90). Used to set Tavily's `days` parameter.

---

#### `_format_result(i, item) → list[str]`  *(private)*

Formats a single Tavily search result (title, content snippet, URL) into a list of indented strings.

---

#### `get_news(ticker, start_date, end_date) → str`

Searches Tavily for company-specific news. For numeric scheme codes (Indian MFs), uses a specialised query like `"Indian mutual fund scheme 105758 NAV performance news"`. For stocks, uses `"{ticker} stock news earnings analysis latest"`. Returns up to 10 formatted results with title, content snippet, and source URL.

---

#### `get_global_news(curr_date, look_back_days=7, limit=10) → str`

Cycles through `_GLOBAL_QUERIES`, calls Tavily for each (5 results per query), deduplicates by title, and returns up to `limit` unique articles.

---

### `dataflows/rss_news.py`

RSS-based news vendor. No API key required.

**Module constant:** `_GLOBAL_RSS_URLS` — list of 5 RSS feed URLs (Google News macro searches, BBC Business, Reuters Business).

#### `_fetch_rss(url: str) → list[dict]`  *(private)*

| Parameter | Description |
|---|---|
| `url` | Any RSS feed URL |

**Returns:** List of `{title, link, date, summary}` dicts parsed from the RSS XML.

**What it does:** Makes a GET request with a browser-like User-Agent. Parses RSS XML using `xml.etree.ElementTree`. Extracts `<item>` tags. For each item, extracts title, link, `pubDate` (parsed using `email.utils.parsedate_to_datetime`), and description (truncated to 200 chars). Silently returns empty list on any parse error.

---

#### `get_news(ticker, start_date, end_date) → str`

Fetches from two RSS sources: Yahoo Finance headline feed and Google News RSS search for `"{ticker} stock news"`. Deduplicates by title. Returns up to 15 articles with date and title (plus optional summary snippet).

---

#### `get_global_news(curr_date, look_back_days=7, limit=10) → str`

Iterates `_GLOBAL_RSS_URLS`, calls `_fetch_rss()` for each, deduplicates by title, and returns up to `limit` unique articles.

---

### `dataflows/newsapi.py`

NewsAPI.org vendor. Requires `NEWSAPI_KEY`. Raises `RuntimeError` on missing key (triggers fallback chain).

#### `get_news(ticker, start_date, end_date) → str`

Calls NewsAPI `/v2/everything` with query `'"{ticker}" stock'`, date range, English language, sorted by relevancy. Returns up to 15 articles with date, source name, title, and description snippet. Raises `RuntimeError` on API errors or missing key.

---

#### `get_global_news(curr_date, look_back_days=7, limit=10) → str`

Calls NewsAPI `/v2/top-headlines` with `category=business&language=en`. Returns up to `limit` business headlines with date and source name.

---

### `dataflows/finnhub.py`

Finnhub vendor. Requires `FINNHUB_KEY`. Raises `RuntimeError` on missing key.

#### `_symbol(ticker: str) → str`  *(private)*

Strips exchange suffix from ticker for Finnhub compatibility. E.g. `"RELIANCE.NS"` → `"RELIANCE"`.

---

#### `get_news(ticker, start_date, end_date) → str`

Calls Finnhub `/api/v1/company-news` with the stripped symbol and date range. Returns up to 15 articles with date (converted from Unix timestamp), source, title, and summary snippet.

---

#### `get_global_news(curr_date, look_back_days=7, limit=10) → str`

Calls Finnhub `/api/v1/news?category=general`. Returns up to `limit` market news articles with date and source.

---

### `dataflows/alpha_vantage_news.py`

Alpha Vantage `NEWS_SENTIMENT` endpoint vendor. Requires `ALPHA_VANTAGE_API_KEY`.

#### `_check_rate_limit(data: dict) → None`  *(private)*

Same as in `alpha_vantage_stock.py` — raises `AlphaVantageRateLimitError` on rate limit detection.

---

#### `get_news(ticker, start_date, end_date) → str`

Calls `NEWS_SENTIMENT` function with ticker, date range (converted to `YYYYMMDDTHHMM` format), and limit 20. Returns up to 20 articles with date, sentiment label, title, and source.

---

#### `get_global_news(curr_date, look_back_days=7, limit=10) → str`

Calls `NEWS_SENTIMENT` with `topics=economy_macro,financial_markets`. Returns up to `limit` articles with date, sentiment, title, and source.

---

## 14. `dataflows` — Sentiment Vendors

---

### `dataflows/reddit.py`

Public Reddit JSON API. No authentication or API key required.

**Module constants:** `_HEADERS` (User-Agent header), `_SUBREDDITS` (`["wallstreetbets", "investing", "stocks"]`).

#### `get_reddit_sentiment(ticker, limit=25) → str`

For each subreddit in `_SUBREDDITS`, calls the Reddit public search API (`/r/{sub}/search.json?q={ticker}&sort=new`), extracts post title, score (upvotes), num_comments, and URL. Aggregates all posts, sorts by score descending, deduplicates, and returns the top `limit` posts formatted as numbered lines with subreddit, score, comment count, and title.

---

### `dataflows/stocktwits.py`

StockTwits public stream API. No authentication required.

#### `get_stocktwits_sentiment(ticker, limit=30) → str`

Calls `https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json`. Extracts `body` (message text), `entities.sentiment.basic` (Bullish / Bearish / Neutral), and `user.username`. Returns up to `limit` messages formatted with sentiment label and username. Handles HTTP errors and timeouts gracefully.

---

### `dataflows/google_trends.py`

Google Trends via `pytrends`. No API key required.

#### `get_google_trends(ticker, look_back_days=30) → str`

| Parameter | Description |
|---|---|
| `ticker` | Ticker symbol (exchange suffix is stripped) |
| `look_back_days` | Lookback window in days (capped at 89 for valid pytrends timeframe syntax) |

**Returns:** Formatted string with trend direction, period average, recent 7-point average, peak/trough, and weekly data table.

**What it does:**
1. Strips exchange suffix from ticker (e.g. `"RELIANCE.NS"` → `"RELIANCE"`).
2. Returns early for numeric scheme codes (no Trends data for MF scheme codes).
3. Calls `TrendReq(hl="en-US", tz=330)` (IST timezone), builds payload with `timeframe="today N-d"`.
4. Fetches `interest_over_time()` DataFrame (values 0–100).
5. Drops `isPartial` column if present.
6. Computes: period average, 7-point recent average, trend direction (Rising / Stable / Falling based on ±15% deviation from average), peak and trough.
7. Returns weekly-sampled data for the last 8 weeks. Raises `RuntimeError` on any failure (triggers fallback chain).

---

### `dataflows/fear_greed.py`

Fear & Greed Index from two free APIs. No key required.

#### `_cnn_fear_greed() → list[str]`  *(private)*

Fetches `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`. Extracts current score and rating from `fear_and_greed` key. Also extracts the last 7 historical readings from `fear_and_greed_historical.data` (each with timestamp in milliseconds, score, and rating label). Returns a list of formatted strings.

---

#### `_alt_fear_greed() → list[str]`  *(private)*

Fetches `https://api.alternative.me/fng/?limit=7&format=json`. Extracts up to 7 daily readings (value 0–100, value_classification, Unix timestamp). Returns a list of formatted date + value + label strings.

---

#### `get_fear_greed(curr_date) → str`

Calls `_cnn_fear_greed()` and `_alt_fear_greed()` separately. Each failure is caught and noted as an unavailability message. Joins both outputs with a blank separator. Raises `RuntimeError` only if both fail (triggers fallback chain).

---

## 15. `dataflows` — Mutual Fund Vendors

---

### `dataflows/mfapi.py`

Primary mutual fund data vendor. Uses `https://api.mfapi.in/mf`. No API key required.

#### `_parse_mfapi_date(date_str: str) → datetime`  *(private)*

Converts MFApi's `"DD-MM-YYYY"` date format to a Python `datetime` object.

---

#### `_fetch_scheme(scheme_code: str) → dict`  *(private)*

Calls `https://api.mfapi.in/mf/{scheme_code}`. Raises `ValueError` if the response status is not `"SUCCESS"`. Returns the full response JSON dict with `meta` (fund info) and `data` (NAV list, newest first).

---

#### `get_fund_nav_history(scheme_code, start_date, end_date) → str`

Fetches the full NAV history via `_fetch_scheme()`, filters entries to the `[start_date, end_date]` range using `_parse_mfapi_date()`, and returns a CSV string (`Date,NAV`) sorted by MFApi's default order (newest first).

---

#### `get_fund_info(scheme_code) → str`

Fetches scheme metadata from `_fetch_scheme()`. Extracts scheme name, fund house, scheme type, scheme category, latest NAV, and NAV date. Returns a labelled key-value text block.

---

#### `get_trailing_returns(scheme_code, benchmark_code="^NSEI") → str`

| Parameter | Description |
|---|---|
| `scheme_code` | Numeric MFApi scheme code |
| `benchmark_code` | yfinance ticker for benchmark (default `"^NSEI"` = Nifty 50) |

**Returns:** A table string with Fund Return and Benchmark return for periods: 1M / 3M / 6M / 1Y / 3Y / 5Y.

**What it does:**
1. Fetches full NAV history and builds a `datetime → float` dict.
2. For each period (e.g. 1Y = 365 days back from latest date), calls `closest_nav()` to find the nearest available NAV on or before that target date.
3. Calculates fund return as `((latest_nav / past_nav) - 1) × 100`.
4. Downloads benchmark via `yf.download()` (5+ years of history). For each period, extracts the benchmark close on or before the target date and calculates benchmark return.
5. Returns a formatted table with `+/-` percentage columns.

**Inner helper — `closest_nav(target_dt) → float | None`:** Finds the most recent NAV date on or before `target_dt` from the sorted NAV map.

---

#### `search_fund(query: str) → str`

Calls `https://api.mfapi.in/mf/search?q={query}`. Returns up to 20 matching funds formatted as numbered lines with scheme code and scheme name.

---

### `dataflows/amfi.py`

Fallback mutual fund data vendor. Uses the official AMFI NAV text file.

#### `get_all_funds() → dict[str, dict]`

Fetches `https://www.amfiindia.com/spages/NAVAll.txt`. Parses the semicolon-separated file line by line:
- Lines starting with a digit are fund data: extracts scheme_code, scheme_name, nav, date.
- Lines containing `"Mutual Fund"`, `"Asset Management"`, or `"AMC"` are AMC headers: sets `current_amc`.
- Other non-digit lines are SEBI category headers: sets `current_category`.

**Returns:** `dict[scheme_code_str → {name, nav, date, category, amc}]`. Returns `{"error": message}` on network failure.

---

#### `get_fund_by_name(name_query: str) → str`

Calls `get_all_funds()`, filters by case-insensitive partial match on fund name. Returns up to 20 matches with scheme code, name, NAV, and NAV date.

---

#### `get_category_funds(category: str) → str`

Calls `get_all_funds()`, filters by case-insensitive partial match on the `category` field. Returns up to 30 funds in that SEBI category.

---

## 16. `graph` — Orchestration Layer

---

### `graph/trading_graph.py`

#### `run(ticker, trade_date, config=None) → dict`

| Parameter | Type | Description |
|---|---|---|
| `ticker` | `str` | Ticker symbol or MFApi scheme code |
| `trade_date` | `str` | Analysis date `"YYYY-MM-DD"` |
| `config` | `dict | None` | Optional config overrides; merged via `get_config()` |

**Returns:** The signal dict with all output keys (ticker, asset_type, trade_date, rating, final_decision, investment_plan, trader_proposal, bull_research, bear_research, and all analyst reports).

**What it does:**
1. `get_config(config)` — resolves full config.
2. `load_past_context(ticker, cfg)` — loads prior decisions from memory store.
3. `build_graph(cfg)` — assembles and compiles the LangGraph StateGraph.
4. `initialise_state(ticker, trade_date, cfg, past_context)` — builds zeroed initial state.
5. `compiled.invoke(initial_state)` — runs the full agent pipeline.
6. `extract_final_signal(result)` — extracts clean output from raw state.
7. `reflect_and_store(ticker, trade_date, signal, cfg)` — persists to memory store.
8. `save_report(signal)` — writes markdown report to `reports/`.
9. Returns the signal dict.

---

### `graph/setup.py`

#### `build_graph(config: dict)`

**Returns:** A compiled LangGraph graph object (either with or without a MemorySaver checkpointer).

**What it does:**
1. Calls `set_config(config)` to make the config available to routers.
2. Creates `deep_llm` and `quick_llm` via `create_llm_client(...).get_llm()`.
3. Instantiates all 13 agent node factory functions with the appropriate LLM.
4. Creates a `StateGraph(AgentState)`.
5. Adds all nodes: 6 analysts + bull + bear + research_manager + trader + 3 risk agents + portfolio_manager.
6. **Edges from START**: calls `get_analyst_node_names(asset_type)` and adds a `START → analyst` edge for each active analyst (parallel fan-out).
7. **Fan-in**: adds an `analyst → bull_researcher` edge for each active analyst (LangGraph waits for all before firing bull_researcher).
8. **Investment debate loop**: adds conditional edges from bull_researcher (→ bear or → research_manager) and from bear_researcher (→ bull or → research_manager), using `make_invest_debate_router()` and `make_bear_router()`.
9. **Linear**: `research_manager → trader → aggressive_debator`.
10. **Risk debate loop**: adds conditional edges from aggressive → conservative or portfolio_manager, from conservative → neutral or portfolio_manager, from neutral → aggressive or portfolio_manager, using `make_risk_debate_router()`.
11. **Terminal**: `portfolio_manager → END`.
12. Gets optional checkpointer via `get_checkpointer(config)` and compiles.

---

### `graph/propagation.py`

#### `initialise_state(ticker, trade_date, config, past_context="") → dict`

| Parameter | Type | Description |
|---|---|---|
| `ticker` | `str` | Ticker or scheme code |
| `trade_date` | `str` | Analysis date |
| `config` | `dict` | Resolved config dict |
| `past_context` | `str` | Prior decisions from memory (default empty) |

**Returns:** A fully zeroed `AgentState` dict suitable for `compiled.invoke()`.

**What it does:** Builds and returns a dict with all `AgentState` fields initialised to their zero values — empty strings for text fields, `0` for counters, empty dicts for nested debate states, and `[]` for LangGraph's internal `messages` list.

---

### `graph/signal_processing.py`

#### `extract_final_signal(result: dict) → dict`

| Parameter | Description |
|---|---|
| `result` | The raw dict returned by `compiled.invoke()` |

**Returns:** A clean signal dict with 16 keys (see Output & Reports section in README).

**What it does:** Reads top-level state keys for analyst reports, investment_plan, trader_investment_plan, and final_trade_decision. Reads `result["investment_debate_state"]["bull_history"]` and `"bear_history"` for the debate outputs. Calls `parse_rating(final_decision)` to extract the 5-tier rating.

---

#### `_section(title: str, content: str) → str`  *(private)*

Returns `"## {title}\n\n{content}\n\n"` if content is non-empty and not the N/A sentinel. Returns `""` otherwise.

---

#### `save_report(signal: dict, output_dir: str | None = None) → str`

| Parameter | Description |
|---|---|
| `signal` | The signal dict from `extract_final_signal()` |
| `output_dir` | Override output directory (default: `reports/` in project root) |

**Returns:** Absolute path of the saved markdown file.

**What it does:**
1. Creates `output_dir` if it doesn't exist.
2. Builds a safe filename by replacing Windows-unsafe characters in the ticker with `_` (handles tickers like `RELIANCE.NS`).
3. Writes a markdown file with a summary table (ticker, asset type, date, rating, generation timestamp) followed by one `## Section` per non-empty signal field in order: Final Decision, Investment Plan, Trader Proposal, Bull Research, Bear Research, Market Analysis, Fundamentals Analysis, News Analysis, Sentiment Analysis, Holdings Analysis, Category Analysis.

---

### `graph/reflection.py`

#### `_load_from_disk() → None`  *(private)*

Reads `memory_store.json` from the project root into the module-level `_memory` dict. Silently no-ops if the file doesn't exist or is malformed.

---

#### `_save_to_disk() → None`  *(private)*

Writes the current `_memory` dict to `memory_store.json` with 2-space indentation. Silently no-ops on any write error.

---

#### `reflect_and_store(ticker, trade_date, signal, config) → None`

| Parameter | Description |
|---|---|
| `ticker` | Asset identifier |
| `trade_date` | Analysis date |
| `signal` | The signal dict |
| `config` | Resolved config dict (unused currently, reserved for future use) |

**What it does:** Loads the current memory store from disk. Creates a new entry dict with `trade_date`, `rating`, `final_decision` (first 200 chars stored as-is), and `stored_at` (UTC ISO timestamp). Appends the entry to `_memory[ticker]`. Saves back to disk.

---

#### `load_past_context(ticker, config) → str`

| Parameter | Description |
|---|---|
| `ticker` | Asset identifier to look up |
| `config` | Used to determine lookback window (30 days for MFs, 5 days for stocks) |

**Returns:** A formatted multi-line string of prior decisions, or `""` if none exist within the window.

**What it does:** Loads memory from disk. Filters entries for the ticker to those within the lookback window (based on `stored_at` UTC timestamp). Takes the last 5 qualifying entries. Formats each as `[trade_date] Rating: X` + a 200-character snippet of the final decision.

---

### `graph/conditional_logic.py`

#### `make_invest_debate_router() → Callable`

**Returns:** A router function `router(state) → str`.

**What the router does:** Reads `investment_debate_state.count` and `config["max_debate_rounds"]`. If `count < max_debate_rounds × 2` (not all rounds complete), returns `"bear_researcher"`. Otherwise returns `"research_manager"`. Called after bull_researcher's node completes.

---

#### `make_bear_router() → Callable`

**Returns:** A router function `router(state) → str`.

**What the router does:** Same threshold check as `make_invest_debate_router()`. If count is still under the threshold, returns `"bull_researcher"` (continue debate). Otherwise returns `"research_manager"` (end debate). Called after bear_researcher's node completes.

---

#### `make_risk_debate_router() → Callable`

**Returns:** A router function `router(state) → str`.

**What the router does:** Reads `risk_debate_state.count`, `config["max_risk_discuss_rounds"]`, and `risk_debate_state.latest_speaker`. If `count >= max_risk_discuss_rounds × 3`, returns `"portfolio_manager"` (all rounds complete). Otherwise uses `latest_speaker` to determine the rotation:
- `"Aggressive"` → returns `"conservative_debator"`
- `"Conservative"` → returns `"neutral_debator"`
- `"Neutral"` or empty → returns `"aggressive_debator"` (start of a new round)

Called after each of the three risk debators' nodes complete.

---

### `graph/analyst_execution.py`

#### `get_analyst_node_names(asset_type: str) → list[str]`

| Parameter | Description |
|---|---|
| `asset_type` | `"stock"` or `"mutual_fund"` |

**Returns:** List of node name strings to register as parallel START edges.

**What it does:**
- `"mutual_fund"` → `["holdings_analyst", "category_analyst", "news_analyst"]`
- Anything else (stocks) → `["market_analyst", "fundamentals_analyst", "news_analyst", "sentiment_analyst"]`

---

### `graph/checkpointer.py`

#### `get_checkpointer(config: dict)`

**Returns:** A `MemorySaver` instance if `config["checkpoint_enabled"]` is `True`, else `None`.

**What it does:** If checkpointing is enabled, lazy-imports and instantiates `langgraph.checkpoint.memory.MemorySaver`. This allows a graph run to be resumed after a crash by replaying from the last saved checkpoint. Passing `None` to `graph.compile()` disables checkpointing entirely.

---

## 17. `llm_clients` — Provider Abstraction

---

### `llm_clients/capabilities.py`

#### `ModelCapabilities` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `supports_tool_choice` | `bool` | Whether the model supports tool-calling with explicit `tool_choice` parameter |
| `supports_json_mode` | `bool` | Whether the model can be forced into JSON output mode |
| `supports_json_schema` | `bool` | Whether the model supports JSON schema-constrained output |
| `preferred_structured_method` | `str` | `"function_calling"`, `"json_mode"`, `"json_schema"`, or `"none"` |
| `requires_reasoning_content_roundtrip` | `bool` | For DeepSeek thinking tokens that need special handling |
| `requires_reasoning_split` | `bool` | For models that return reasoning and response in separate blocks |

The registry `CAPABILITIES` maps model name strings to `ModelCapabilities` instances for all supported models across OpenAI, Anthropic, Google, Groq, DeepSeek, xAI, and common Ollama models.

`DEFAULT_CAPABILITIES` — all-False safe default for unknown models.

---

#### `get_capabilities(model: str) → ModelCapabilities`

| Parameter | Description |
|---|---|
| `model` | Model name string |

**Returns:** The matching `ModelCapabilities` instance.

**What it does:** Tries exact match in `CAPABILITIES` dict first. If not found, tries prefix match (e.g. a fine-tuned model that starts with a known base name). If neither matches, returns `DEFAULT_CAPABILITIES`.

---

### `llm_clients/base_client.py`

#### `BaseLLMClient` (ABC)

Abstract base class for all LLM provider wrappers.

**Abstract method — `get_llm() → BaseChatModel`:** Must be implemented by every subclass. Returns the underlying LangChain `BaseChatModel` that agents can call `bind_tools()`, `with_structured_output()`, and `invoke()` on.

**Static method — `normalize_content(response) → str`:** Flattens list-of-typed-blocks LLM responses to a plain string. Handles providers (OpenAI Responses API, Google Gemini 3.x) that return content as a list of `{"type": "text", "text": "..."}` dicts. Text blocks are joined; reasoning/tool_use blocks are discarded.

---

### `llm_clients/api_key_env.py`

**Module constant:** `PROVIDER_API_KEY_ENV` — maps provider name → env var name (`"openai"` → `"OPENAI_API_KEY"`, etc.). Ollama maps to `None` (no key needed).

#### `get_api_key_env(provider: str) → str | None`

Returns the env var name for the given provider's API key, or `None` if no key is needed.

---

#### `ensure_api_key(provider: str) → None`

Raises `EnvironmentError` with a clear message if the required API key env var is empty or unset. No-ops for Ollama. Called by `create_llm_client()` before instantiating the client.

---

### `llm_clients/validators.py`

#### `validate_provider(provider: str) → None`

Raises `ValueError` if `provider` is not in `get_all_providers()`. Lists all supported providers in the error message.

---

#### `validate_model(provider: str, model: str) → None`

Raises `ValueError` if `model` is not in the provider's catalog — but only for fixed-catalog providers. For open-catalog providers (Ollama, OpenRouter), whose model list is `[]` in `MODEL_CATALOG`, any model name is accepted.

---

### `llm_clients/model_catalog.py`

**Module constant:** `MODEL_CATALOG` — dict mapping provider name → list of curated model name strings. Open-catalog providers (`"openrouter"`, `"ollama"`) map to `[]`.

#### `get_models_for_provider(provider: str) → list[str]`

Returns the model list for the given provider. Empty list means open catalog.

---

#### `get_all_providers() → list[str]`

Returns the list of all supported provider names (the keys of `MODEL_CATALOG`).

---

### `llm_clients/factory.py`

#### `create_llm_client(provider, model, base_url=None, **kwargs) → BaseLLMClient`

| Parameter | Type | Description |
|---|---|---|
| `provider` | `str` | Provider name (e.g. `"openai"`, `"groq"`) |
| `model` | `str` | Model name (e.g. `"gpt-4o"`) |
| `base_url` | `str | None` | Override base URL (required for Ollama, optional for others) |
| `**kwargs` | | Extra keyword args forwarded to the client constructor |

**Returns:** A `BaseLLMClient` subclass instance. Call `.get_llm()` on it to get the LangChain model.

**What it does:** Calls `validate_provider()` and `ensure_api_key()`. Uses a `match` statement to lazy-import and instantiate the correct client class:
- `"openai"`, `"xai"`, `"deepseek"`, `"openrouter"` → `OpenAIClient`
- `"anthropic"` → `AnthropicClient`
- `"google"` → `GoogleClient`
- `"groq"` → `GroqClient`
- `"ollama"` → `OllamaClient`

---

### `llm_clients/openai_client.py`

#### `OpenAIClient.__init__(provider, model, base_url=None, **kwargs)`

Resolves the base URL from `_BASE_URLS` (maps `"xai"` → xAI API, `"deepseek"` → DeepSeek API, `"openrouter"` → OpenRouter API). Instantiates `ChatOpenAI(model=model, base_url=resolved_url, ...)`.

#### `OpenAIClient.get_llm() → ChatOpenAI`

Returns the `ChatOpenAI` instance.

---

### `llm_clients/anthropic_client.py`

#### `AnthropicClient.__init__(model, **kwargs)`

Instantiates `ChatAnthropic(model=model, ...)`.

#### `AnthropicClient.get_llm() → ChatAnthropic`

Returns the `ChatAnthropic` instance.

---

### `llm_clients/google_client.py`

#### `GoogleClient.__init__(model, **kwargs)`

Instantiates `ChatGoogleGenerativeAI(model=model, ...)`.

#### `GoogleClient.get_llm() → ChatGoogleGenerativeAI`

Returns the `ChatGoogleGenerativeAI` instance.

---

### `llm_clients/groq_client.py`

#### `GroqClient.__init__(model, **kwargs)`

Instantiates `ChatGroq(model=model, ...)`.

#### `GroqClient.get_llm() → ChatGroq`

Returns the `ChatGroq` instance.

---

### `llm_clients/ollama_client.py`

#### `OllamaClient.__init__(model, base_url="http://localhost:11434", **kwargs)`

| Parameter | Description |
|---|---|
| `base_url` | Ollama server URL (default localhost) |

Instantiates `ChatOllama(model=model, base_url=base_url, ...)`.

#### `OllamaClient.get_llm() → ChatOllama`

Returns the `ChatOllama` instance.

---

*End of Codebase Reference — all files, all functions, all parameters documented.*
