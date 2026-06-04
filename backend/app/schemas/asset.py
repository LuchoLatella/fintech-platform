from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────

class AssetBase(BaseModel):

    symbol: str
    name: str

    exchange_id: Optional[int] = None
    asset_class_id: Optional[int] = None

    description: Optional[str] = None

    currency: str = "USD"

    isin: Optional[str] = None

    sector: Optional[str] = None
    industry: Optional[str] = None

    country: Optional[str] = None

    is_active: bool = True
    is_argentine: bool = False

    underlying_symbol: Optional[str] = None

    ratio: Optional[float] = None


# ─────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────

class AssetCreate(AssetBase):
    pass


# ─────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────

class AssetUpdate(BaseModel):

    symbol: Optional[str] = None
    name: Optional[str] = None

    exchange_id: Optional[int] = None
    asset_class_id: Optional[int] = None

    description: Optional[str] = None

    currency: Optional[str] = None

    isin: Optional[str] = None

    sector: Optional[str] = None
    industry: Optional[str] = None

    country: Optional[str] = None

    is_active: Optional[bool] = None
    is_argentine: Optional[bool] = None

    underlying_symbol: Optional[str] = None

    ratio: Optional[float] = None


# ─────────────────────────────────────────────
# Response
# ─────────────────────────────────────────────

class AssetResponse(AssetBase):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID

    created_at: datetime
    updated_at: Optional[datetime] = None