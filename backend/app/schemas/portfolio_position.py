from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PortfolioPositionBase(BaseModel):
    asset_id: UUID
    quantity: float
    avg_cost: float
    currency: str = "USD"
    notes: Optional[str] = None


class PortfolioPositionCreate(PortfolioPositionBase):
    pass


class PortfolioPositionUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    is_open: Optional[bool] = None


class PortfolioPositionResponse(PortfolioPositionBase):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    portfolio_id: UUID

    is_open: bool

    opened_at: datetime
    closed_at: Optional[datetime]