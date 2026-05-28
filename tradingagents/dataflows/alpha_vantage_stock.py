import os
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData

from .utils import AlphaVantageRateLimitError

_AV_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
_RATE_LIMIT_MSG = "Thank you for using Alpha Vantage"


def _check_rate_limit(data: dict) -> None:
    note = data.get("Note", "") or data.get("Information", "")
    if _RATE_LIMIT_MSG in note:
        raise AlphaVantageRateLimitError("Alpha Vantage rate limit reached")


def get_stock_data(symbol: str, start_date: str, end_date: str) -> str:
    try:
        ts = TimeSeries(key=_AV_KEY, output_format="pandas")
        df, _ = ts.get_daily_adjusted(symbol=symbol, outputsize="full")
        _check_rate_limit({})
        df.index = df.index.astype(str)
        mask = (df.index >= start_date) & (df.index <= end_date)
        df   = df[mask][["1. open", "2. high", "3. low", "4. close", "6. volume"]]
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        return df.sort_index().to_csv() if not df.empty else f"No data for {symbol}"
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching stock data for {symbol}: {e}"


def get_fundamentals(ticker: str, curr_date: str) -> str:
    try:
        fd   = FundamentalData(key=_AV_KEY, output_format="json")
        data, _ = fd.get_company_overview(symbol=ticker)
        _check_rate_limit(data)
        fields = [
            "Name", "Sector", "Industry", "MarketCapitalization",
            "TrailingPE", "ForwardPE", "PriceToBookRatio", "PriceToSalesRatioTTM",
            "EVToEBITDA", "ReturnOnEquityTTM", "ReturnOnAssetsTTM",
            "ProfitMargin", "GrossProfitTTM", "DebtToEquityRatio",
            "CurrentRatio", "DividendYield", "52WeekHigh", "52WeekLow", "Beta",
            "AnalystTargetPrice",
        ]
        lines = [f"{f}: {data.get(f, 'N/A')}" for f in fields]
        return f"Fundamentals for {ticker} (Alpha Vantage):\n" + "\n".join(lines)
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching fundamentals for {ticker}: {e}"


def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    try:
        fd = FundamentalData(key=_AV_KEY, output_format="pandas")
        df, _ = fd.get_balance_sheet_quarterly(symbol=ticker) if freq == "quarterly" \
                else fd.get_balance_sheet_annual(symbol=ticker)
        _check_rate_limit({})
        return f"Balance Sheet ({freq}) for {ticker} — Alpha Vantage:\n{df.to_string()}"
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching balance sheet for {ticker}: {e}"


def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    try:
        fd = FundamentalData(key=_AV_KEY, output_format="pandas")
        df, _ = fd.get_cash_flow_quarterly(symbol=ticker) if freq == "quarterly" \
                else fd.get_cash_flow_annual(symbol=ticker)
        _check_rate_limit({})
        return f"Cash Flow ({freq}) for {ticker} — Alpha Vantage:\n{df.to_string()}"
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching cash flow for {ticker}: {e}"


def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    try:
        fd = FundamentalData(key=_AV_KEY, output_format="pandas")
        df, _ = fd.get_income_statement_quarterly(symbol=ticker) if freq == "quarterly" \
                else fd.get_income_statement_annual(symbol=ticker)
        _check_rate_limit({})
        return f"Income Statement ({freq}) for {ticker} — Alpha Vantage:\n{df.to_string()}"
    except AlphaVantageRateLimitError:
        raise
    except Exception as e:
        return f"Alpha Vantage error fetching income statement for {ticker}: {e}"
