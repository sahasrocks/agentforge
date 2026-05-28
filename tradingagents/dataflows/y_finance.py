from datetime import datetime
import yfinance as yf
import pandas as pd

from .utils import get_date_range, format_number


# ── Price Data ─────────────────────────────────────────────────────────────────

def get_stock_data(symbol: str, start_date: str, end_date: str) -> str:
    try:
        t = yf.Ticker(symbol)
        df = t.history(start=start_date, end=end_date, auto_adjust=True)
        if df.empty:
            return f"No price data found for {symbol} between {start_date} and {end_date}."
        df.index = df.index.strftime("%Y-%m-%d")
        return df[["Open", "High", "Low", "Close", "Volume"]].round(4).to_csv()
    except Exception as e:
        return f"Error fetching stock data for {symbol}: {e}"


# ── Fundamentals ───────────────────────────────────────────────────────────────

def get_fundamentals(ticker: str, curr_date: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        fields = {
            "Company":            info.get("longName", "N/A"),
            "Sector":             info.get("sector", "N/A"),
            "Industry":           info.get("industry", "N/A"),
            "Market Cap":         format_number(info.get("marketCap")),
            "Enterprise Value":   format_number(info.get("enterpriseValue")),
            "Trailing P/E":       info.get("trailingPE", "N/A"),
            "Forward P/E":        info.get("forwardPE", "N/A"),
            "Price/Book":         info.get("priceToBook", "N/A"),
            "Price/Sales":        info.get("priceToSalesTrailing12Months", "N/A"),
            "EV/EBITDA":          info.get("enterpriseToEbitda", "N/A"),
            "Return on Equity":   info.get("returnOnEquity", "N/A"),
            "Return on Assets":   info.get("returnOnAssets", "N/A"),
            "Profit Margin":      info.get("profitMargins", "N/A"),
            "Gross Margin":       info.get("grossMargins", "N/A"),
            "Debt/Equity":        info.get("debtToEquity", "N/A"),
            "Current Ratio":      info.get("currentRatio", "N/A"),
            "Quick Ratio":        info.get("quickRatio", "N/A"),
            "Revenue (TTM)":      format_number(info.get("totalRevenue")),
            "Earnings (TTM)":     format_number(info.get("netIncomeToCommon")),
            "Free Cash Flow":     format_number(info.get("freeCashflow")),
            "Dividend Yield":     info.get("dividendYield", "N/A"),
            "52W High":           info.get("fiftyTwoWeekHigh", "N/A"),
            "52W Low":            info.get("fiftyTwoWeekLow", "N/A"),
            "Beta":               info.get("beta", "N/A"),
            "Analyst Target":     info.get("targetMeanPrice", "N/A"),
            "Recommendation":     info.get("recommendationKey", "N/A"),
        }
        lines = [f"{k}: {v}" for k, v in fields.items()]
        return f"Fundamentals for {ticker} (as of {curr_date})\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching fundamentals for {ticker}: {e}"


def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    try:
        t = yf.Ticker(ticker)
        df = t.quarterly_balance_sheet if freq == "quarterly" else t.balance_sheet
        if df is None or df.empty:
            return f"No balance sheet data available for {ticker}."
        df.columns = [str(c)[:10] for c in df.columns]
        return f"Balance Sheet ({freq}) for {ticker}:\n{df.to_string()}"
    except Exception as e:
        return f"Error fetching balance sheet for {ticker}: {e}"


def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    try:
        t = yf.Ticker(ticker)
        df = t.quarterly_cashflow if freq == "quarterly" else t.cashflow
        if df is None or df.empty:
            return f"No cash flow data available for {ticker}."
        df.columns = [str(c)[:10] for c in df.columns]
        return f"Cash Flow Statement ({freq}) for {ticker}:\n{df.to_string()}"
    except Exception as e:
        return f"Error fetching cash flow for {ticker}: {e}"


def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    try:
        t = yf.Ticker(ticker)
        df = t.quarterly_income_stmt if freq == "quarterly" else t.income_stmt
        if df is None or df.empty:
            return f"No income statement data available for {ticker}."
        df.columns = [str(c)[:10] for c in df.columns]
        return f"Income Statement ({freq}) for {ticker}:\n{df.to_string()}"
    except Exception as e:
        return f"Error fetching income statement for {ticker}: {e}"


# ── News ───────────────────────────────────────────────────────────────────────

def _format_news_item(i: int, item: dict) -> str:
    title     = item.get("title", "No title")
    publisher = item.get("publisher", "Unknown")
    ts        = item.get("providerPublishTime", 0)
    date_str  = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "N/A"
    return f"{i}. [{date_str}] {title} — {publisher}"


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    try:
        news = yf.Ticker(ticker).news
        if not news:
            return f"No news found for {ticker}."

        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts   = int(datetime.strptime(end_date,   "%Y-%m-%d").timestamp())

        filtered = [
            n for n in news
            if start_ts <= n.get("providerPublishTime", 0) <= end_ts
        ]
        if not filtered:
            filtered = news  # fall back to all available if date filter returns nothing

        lines = [_format_news_item(i + 1, n) for i, n in enumerate(filtered[:20])]
        return f"News for {ticker} ({start_date} to {end_date}):\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching news for {ticker}: {e}"


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    try:
        # Use broad market proxies to pull macro/global news
        proxies  = ["^GSPC", "^DJI", "^IXIC"]
        seen     = set()
        articles = []

        start_date, _ = get_date_range(curr_date, look_back_days)
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts   = int(datetime.strptime(curr_date,  "%Y-%m-%d").timestamp())

        for proxy in proxies:
            for item in yf.Ticker(proxy).news or []:
                title = item.get("title", "")
                if title in seen:
                    continue
                seen.add(title)
                ts = item.get("providerPublishTime", 0)
                if start_ts <= ts <= end_ts:
                    articles.append(item)

        articles = articles[:limit] if articles else articles
        if not articles:
            return "No global market news found for the specified period."

        lines = [_format_news_item(i + 1, n) for i, n in enumerate(articles)]
        return f"Global Market News ({start_date} to {curr_date}):\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching global news: {e}"


def get_insider_transactions(ticker: str) -> str:
    try:
        t  = yf.Ticker(ticker)
        df = t.insider_transactions
        if df is None or df.empty:
            return f"No insider transaction data available for {ticker}."
        return f"Insider Transactions for {ticker}:\n{df.to_string()}"
    except Exception as e:
        return f"Error fetching insider transactions for {ticker}: {e}"
