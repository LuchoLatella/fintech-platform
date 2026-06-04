from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ============================================================
# WATCHLIST
# ============================================================

class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


class WatchlistResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    is_default: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ============================================================
# WATCHLIST ITEMS
# ============================================================

class WatchlistItemCreate(BaseModel):
    asset_id: UUID
    notes: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    id: UUID
    watchlist_id: UUID
    asset_id: UUID
    added_at: datetime
    notes: Optional[str]

    model_config = {
        "from_attributes": True
    }