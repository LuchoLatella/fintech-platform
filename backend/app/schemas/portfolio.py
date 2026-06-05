"""
Schemas Portfolio
"""

from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ==========================================================
# PORTFOLIO
# ==========================================================

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    currency: str = "USD"
    portfolio_type: str = "real"
    is_default: bool = False
    broker: Optional[str] = None
    broker_account: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    portfolio_type: Optional[str] = None
    is_default: Optional[bool] = None
    broker: Optional[str] = None
    broker_account: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: UUID
    user_id: UUID

    name: str
    description: Optional[str]

    currency: str
    portfolio_type: str

    is_default: bool

    broker: Optional[str]
    broker_account: Optional[str]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# POSITIONS
# ==========================================================

class PositionResponse(BaseModel):
    id: UUID

    portfolio_id: UUID
    asset_id: UUID

    quantity: Decimal
    avg_cost: Decimal

    currency: str

    opened_at: datetime
    closed_at: Optional[datetime]

    is_open: bool

    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# TRANSACTIONS
# ==========================================================

class TransactionCreate(BaseModel):
    asset_id: UUID

    transaction_type: str

    quantity: Decimal

    price: Decimal

    commission: Decimal = Decimal("0")

    currency: str = "USD"

    fx_rate: Decimal = Decimal("1")

    notes: Optional[str] = None

    executed_at: datetime


class TransactionResponse(BaseModel):
    id: UUID

    portfolio_id: UUID
    asset_id: UUID

    transaction_type: str

    quantity: Decimal

    price: Decimal

    commission: Decimal

    currency: str

    fx_rate: Decimal

    notes: Optional[str]

    executed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# SNAPSHOTS
# ==========================================================

class PortfolioSnapshotResponse(BaseModel):
    id: int

    portfolio_id: UUID

    snapshot_date: date

    total_value_usd: Optional[Decimal]
    total_value_ars: Optional[Decimal]

    daily_return: Optional[Decimal]
    total_return: Optional[Decimal]

    cash_balance: Optional[Decimal]

    positions_data: Optional[dict]
    metrics: Optional[dict]

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# SUMMARY
# (para el futuro Copilot)
# ==========================================================

class PortfolioSummary(BaseModel):
    portfolio_id: UUID

    total_positions: int

    total_value_usd: Decimal

    cash_balance: Decimal

    total_return: Optional[Decimal] = None

    risk_score: Optional[Decimal] = None

    recommendation_count: int = 0