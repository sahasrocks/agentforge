from typing import TypedDict
from langgraph.graph import MessagesState

class InvestDebateState(TypedDict): #Tracks the bull vs bear debate between researchers.
    bull_history: str       # bull's cumulative arguments across all rounds
    bear_history: str       # bear's cumulative arguments across all rounds
    history: str            # combined transcript of the full debate
    current_response: str   # the latest message (used for routing)
    judge_decision: str     # Research Manager's final verdict
    count: int              # round counter — debate ends at 2 × max_debate_rounds

class RiskDebateState(TypedDict): #Tracks the three-way risk debate between aggressive, conservative, and neutral analysts.
    aggressive_history: str
    conservative_history: str
    neutral_history: str
    history: str                        # combined transcript
    latest_speaker: str                 # "Aggressive" | "Conservative" | "Neutral"
    current_aggressive_response: str
    current_conservative_response: str
    current_neutral_response: str
    judge_decision: str                 # Portfolio Manager's final verdict
    count: int                          # ends at 3 × max_risk_discuss_rounds

class AgentState(MessagesState):
    # Identity
    company_of_interest: str    # ticker symbol e.g. "RELIANCE.NS" or scheme code "119598"
    asset_type: str             # "stock" | "mutual_fund"
    trade_date: str             # "YYYY-MM-DD"
    sender: str                 # name of the last agent that wrote to state

    # Analyst outputs — stocks
    market_report: str
    sentiment_report: str
    news_report: str
    fundamentals_report: str

    # Analyst outputs — mutual funds (new)
    holdings_report: str        # Holdings Analyst output
    category_report: str        # Category Analyst output

    # Fund-specific identity (new)
    fund_benchmark: str         # fund's declared benchmark ticker e.g. "^NSEI"

    # Investment debate
    investment_debate_state: InvestDebateState
    investment_plan: str        # Research Manager's final markdown

    # Trading
    trader_investment_plan: str # Trader's proposal markdown

    # Risk debate
    risk_debate_state: RiskDebateState
    final_trade_decision: str   # Portfolio Manager's final markdown

    # Memory injection
    past_context: str           # prior decisions injected at run start
