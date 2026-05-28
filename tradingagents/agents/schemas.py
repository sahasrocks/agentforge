from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class PortfolioRating(str, Enum):
    BUY         = "Buy"
    OVERWEIGHT  = "Overweight"
    HOLD        = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL        = "Sell"
    
class TraderAction(str, Enum):
    BUY  = "Buy"
    HOLD = "Hold"
    SELL = "Sell"
   
class ResearchPlan(BaseModel):
    recommendation:    PortfolioRating
    rationale:         str = Field(description="Why this rating — key evidence from the debate")
    strategic_actions: str = Field(description="Specific actions or levels to watch")

class TraderProposal(BaseModel):
    action:          TraderAction
    reasoning:       str    = Field(description="Why this action given the research plan")
    entry_price:     Optional[float] = Field(None, description="Suggested entry price")
    stop_loss:       Optional[float] = Field(None, description="Stop loss level")
    position_sizing: Optional[str]   = Field(None, description="e.g. '5% of portfolio'")

class PortfolioDecision(BaseModel):
    rating:            PortfolioRating
    executive_summary: str = Field(description="2-3 sentence plain-English summary")
    investment_thesis: str = Field(description="Core bull/bear case that won")
    price_target:      Optional[float] = Field(None, description="12-month price target")
    risk_factors:      Optional[str]   = Field(None, description="Key risks to the thesis")
    time_horizon:      Optional[str]   = Field(None, description="e.g. '6-12 months'")
