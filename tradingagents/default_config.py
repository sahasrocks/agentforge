import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ─────────────────────────────────────────────────────────────────
os.environ["OPENAI_API_KEY"]     = os.getenv("OPENAI_API_KEY", "")
os.environ["ANTHROPIC_API_KEY"]  = os.getenv("ANTHROPIC_API_KEY", "")
os.environ["GOOGLE_API_KEY"]     = os.getenv("GOOGLE_API_KEY", "")
os.environ["GROQ_API_KEY"]       = os.getenv("GROQ_API_KEY", "")
os.environ["TAVILY_API_KEY"]     = os.getenv("TAVILY_API_KEY", "")
os.environ["DEEPSEEK_API_KEY"]   = os.getenv("DEEPSEEK_API_KEY", "")
os.environ["XAI_API_KEY"]        = os.getenv("XAI_API_KEY", "")
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
os.environ["ALPHA_VANTAGE_API_KEY"] = os.getenv("ALPHA_VANTAGE_API_KEY", "")
os.environ["NEWSAPI_KEY"]           = os.getenv("NEWSAPI_KEY", "")
os.environ["FINNHUB_KEY"]           = os.getenv("FINNHUB_KEY", "")


DEFAULT_CONFIG = {
    # ─── Paths ────────────────────────────────────────────────────────────────
    "results_dir":            "~/.tradingagents/logs",
    "data_cache_dir":         "~/.tradingagents/cache",
    "memory_log_path":        "~/.tradingagents/memory/trading_memory.md",
    "memory_log_max_entries": None,           # None = no rotation

    # ─── LLM ──────────────────────────────────────────────────────────────────
    "llm_provider":    "openai",              # openai | anthropic | google | groq | ollama | deepseek | xai | openrouter
    "deep_think_llm":  "gpt-4o",             # analysts, researchers, managers (heavy reasoning)
    "quick_think_llm": "gpt-4o-mini",        # reflector only (lightweight)
    "backend_url":     None,                  # None = provider default; required for Ollama (http://localhost:11434)
    "output_language": "English",

    # Provider-specific reasoning controls (None = disabled)
    "openai_reasoning_effort": None,          # "high" | "medium" | "low"
    "anthropic_effort":        None,          # "high" | "medium" | "low"
    "google_thinking_level":   None,          # "high" | "minimal"

    # ─── Graph / Debate ───────────────────────────────────────────────────────
    "max_debate_rounds":          1,          # Bull+Bear cycles      = 2 × this
    "max_risk_discuss_rounds":    1,          # Agg+Con+Neu cycles    = 3 × this
    "max_recur_limit":            100,        # LangGraph recursion safety cap
    "analyst_concurrency_limit":  1,          # 1 = serial (avoids message ordering bugs)
    "checkpoint_enabled":         False,      # SQLite resume on crash

    # ─── Analyst Selection ────────────────────────────────────────────────────
    # Stocks:       "market" | "sentiment" | "news" | "fundamentals"
    # Mutual funds: "market" | "sentiment" | "holdings" | "category"
    "selected_analysts": ["market", "sentiment", "news", "fundamentals"],

    # ─── News ─────────────────────────────────────────────────────────────────
    "news_article_limit":        20,
    "global_news_article_limit": 10,
    "global_news_lookback_days": 7,
    "global_news_queries": [
        "Federal Reserve interest rates inflation",
        "S&P 500 earnings GDP economic outlook",
        "geopolitical risk trade war sanctions",
        "ECB Bank of England BOJ central bank policy",
        "oil commodities supply chain energy",
    ],

    # ─── Data Vendors — Stocks ────────────────────────────────────────────────
    "data_vendors": {
        "core_stock_apis":      "yfinance",   # get_stock_data
        "technical_indicators": "yfinance",   # get_indicators
        "fundamental_data":     "yfinance",   # get_fundamentals, balance_sheet, etc.
        "news_data":            "tavily",     # get_news, get_global_news
        "sentiment_data":       "reddit",     # get_reddit_sentiment (default)
    },
    # Tool-level overrides — take precedence over data_vendors
    # Single-vendor sentiment tools are pinned here so routing is direct
    "tool_vendors": {
        "get_reddit_sentiment":     "reddit",
        "get_stocktwits_sentiment": "stocktwits",
        "get_google_trends":        "google_trends",
        "get_fear_greed":           "fear_greed",
    },

    # ─── Data Vendors — Mutual Funds ──────────────────────────────────────────
    "fund_data_vendors": {
        "nav_data":  "mfapi",                 # NAV history (Indian funds)
        "fund_info": "mfapi",                 # fund metadata (name, category, AMC)
    },
    "fund_region":         "IN",              # "IN" = India | "US" = United States
    "holding_period_days": 30,                # reflection window: 5 for stocks, 30 for MFs

    # ─── Asset Type ───────────────────────────────────────────────────────────
    # Overridden at runtime via CLI or programmatic call
    "asset_type": "stock",                    # "stock" | "mutual_fund"

    # ─── Benchmark — Stocks ───────────────────────────────────────────────────
    "benchmark_ticker": None,                 # None = auto-detect from ticker suffix
    "benchmark_map": {
        ".NS": "^NSEI",                       # India — NSE
        ".BO": "^BSESN",                      # India — BSE
        ".T":  "^N225",                       # Japan
        ".HK": "^HSI",                        # Hong Kong
        ".L":  "^FTSE",                       # London
        ".TO": "^GSPTSE",                     # Toronto
        ".AX": "^AXJO",                       # Australia
        "":    "SPY",                         # US default
    },

    # ─── Benchmark — Mutual Funds (India) ────────────────────────────────────
    "fund_category_benchmarks": {
        "Large Cap Fund":          "^NSEI",
        "Mid Cap Fund":            "^NSEMDCP50",
        "Small Cap Fund":          "^NSESMLCP250",
        "Flexi Cap Fund":          "^NSEI",
        "Multi Cap Fund":          "^NSEI",
        "ELSS":                    "^NSEI",
        "Balanced Advantage Fund": "^NSEI",
        "Aggressive Hybrid Fund":  "^NSEI",
        "Liquid Fund":             None,      # no equity benchmark
        "Overnight Fund":          None,
        "Short Duration Fund":     None,
        "Corporate Bond Fund":     None,
    },
}


# ─── Environment Variable Override Loader ─────────────────────────────────────
# Any scalar key in DEFAULT_CONFIG can be overridden via TRADINGAGENTS_<KEY>.
# Examples:
#   TRADINGAGENTS_LLM_PROVIDER=groq
#   TRADINGAGENTS_DEEP_THINK_LLM=llama-3.3-70b-versatile
#   TRADINGAGENTS_MAX_DEBATE_ROUNDS=3
#   TRADINGAGENTS_CHECKPOINT_ENABLED=true
#   TRADINGAGENTS_FUND_REGION=IN
#   TRADINGAGENTS_OUTPUT_LANGUAGE=Hindi

def _apply_env_overrides(config: dict) -> dict:
    result = config.copy()
    prefix = "TRADINGAGENTS_"

    for key in result:
        env_key = prefix + key.upper()
        value = os.environ.get(env_key)
        if value is None:
            continue

        original = result[key]

        if isinstance(original, bool):
            result[key] = value.lower() in ("1", "true", "yes")
        elif isinstance(original, int):
            result[key] = int(value)
        elif isinstance(original, float):
            result[key] = float(value)
        else:
            # str, None, list, dict — store as string; caller parses if needed
            result[key] = value

    return result


def get_config(overrides: dict | None = None) -> dict:
    """Return config with env var overrides and optional caller-supplied overrides applied."""
    config = _apply_env_overrides(DEFAULT_CONFIG.copy())
    if overrides:
        config.update(overrides)
    return config
