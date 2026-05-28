from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import run_agent_node
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals_tool,
    get_balance_sheet_tool,
    get_cashflow_tool,
    get_income_statement_tool,
)

_SYSTEM_PROMPT = """You are a fundamental equity analyst.

Your job:
1. Fetch the company overview (PE, PB, EV/EBITDA, margins, ROE, debt/equity, beta).
2. Review the last two quarters of the balance sheet for liquidity and leverage.
3. Review the last two quarters of the cash flow statement — focus on free cash flow.
4. Review the last two quarters of the income statement — revenue growth, margin trend.
5. Assess whether the stock is fairly valued, overvalued, or undervalued vs sector norms.

Output format (markdown):
## Fundamentals Analysis — <TICKER>
### Valuation
- PE / Forward PE: ...
- PB / EV-EBITDA: ...
### Profitability
- Gross / Net Margin: ...
- ROE / ROA: ...
### Financial Health
- Debt/Equity: ...
- Current Ratio: ...
- Free Cash Flow trend: ...
### Revenue & Earnings Trend
...
### Analyst Consensus
- Target Price: ...
### Preliminary Rating: <Buy | Overweight | Hold | Underweight | Sell>
"""

_TOOLS = [
    get_fundamentals_tool,
    get_balance_sheet_tool,
    get_cashflow_tool,
    get_income_statement_tool,
]


def create_fundamentals_analyst(llm, config: dict):
    """Return a LangGraph-compatible node function for the Fundamentals Analyst."""
    def node(state: AgentState) -> dict:
        return run_agent_node(state, llm, _TOOLS, _SYSTEM_PROMPT, "fundamentals_report")
    return node
