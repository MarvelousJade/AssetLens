from typing import Literal

from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    benchmark: str = "^GSPTSE"
    benchmark_name: str = "S&P/TSX Composite"


class PortfolioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    archived: bool | None = None


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    scenario_type: Literal[
        "equity_decline",
        "technology_decline",
        "interest_rate_increase",
        "currency_movement",
        "custom",
    ]
    shocks: dict[str, float] = Field(default_factory=dict)


class CopilotQuestion(BaseModel):
    portfolio_id: str
    question: str = Field(min_length=3, max_length=1000)


class AlertCreate(BaseModel):
    symbol: str
    direction: Literal["above", "below"]
    threshold: float = Field(gt=0)
