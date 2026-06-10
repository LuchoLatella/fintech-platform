from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PortfolioTransactionBase(BaseModel):

    asset_id: UUID

    transaction_type: str

    quantity: Decimal

    price: Decimal

    commission: Decimal = 0

    currency: str = "USD"

    fx_rate: Decimal = 1

    notes: Optional[str] = None

    executed_at: datetime


class PortfolioTransactionCreate(
    PortfolioTransactionBase
):
    pass


class PortfolioTransactionUpdate(BaseModel):

    quantity: Optional[Decimal] = None

    price: Optional[Decimal] = None

    commission: Optional[Decimal] = None

    notes: Optional[str] = None


class PortfolioTransactionResponse(
    PortfolioTransactionBase
):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID

    portfolio_id: UUID

    created_at: datetime

    