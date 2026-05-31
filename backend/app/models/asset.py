"""
Modelos ORM:
- Asset
- AssetClass
- Exchange
- Watchlist
- WatchlistItem
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Text,
    Numeric,
    Integer,
    ForeignKey,
)

from sqlalchemy.dialects.postgresql import UUID, JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.sql import func

from app.database import Base


# ─────────────────────────────────────────────────────────────
# Asset Classes
# ─────────────────────────────────────────────────────────────

class AssetClass(Base):

    __tablename__ = "asset_classes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # RELATIONSHIPS
    assets = relationship(
        "Asset",
        back_populates="asset_class",
        lazy="selectin",
    )


# ─────────────────────────────────────────────────────────────
# Exchanges
# ─────────────────────────────────────────────────────────────

class Exchange(Base):

    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    country: Mapped[Optional[str]] = mapped_column(
        String(5)
    )

    currency: Mapped[Optional[str]] = mapped_column(
        String(5)
    )

    timezone: Mapped[Optional[str]] = mapped_column(
        String(50)
    )

    # RELATIONSHIPS
    assets = relationship(
        "Asset",
        back_populates="exchange",
        lazy="selectin",
    )


# ─────────────────────────────────────────────────────────────
# Assets
# ─────────────────────────────────────────────────────────────

class Asset(Base):

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    symbol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    exchange_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("exchanges.id"),
    )

    asset_class_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("asset_classes.id"),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text
    )

    currency: Mapped[str] = mapped_column(
        String(5),
        default="USD",
    )

    isin: Mapped[Optional[str]] = mapped_column(
        String(20)
    )

    sector: Mapped[Optional[str]] = mapped_column(
        String(100)
    )

    industry: Mapped[Optional[str]] = mapped_column(
        String(100)
    )

    country: Mapped[Optional[str]] = mapped_column(
        String(5)
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    is_argentine: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    underlying_symbol: Mapped[Optional[str]] = mapped_column(
        String(30)
    )

    ratio: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4)
    )

    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ─────────────────────────────────────────────────────────
    # RELATIONSHIPS
    # ─────────────────────────────────────────────────────────

    exchange = relationship(
        "Exchange",
        back_populates="assets",
        lazy="joined",
    )

    asset_class = relationship(
        "AssetClass",
        back_populates="assets",
        lazy="joined",
    )

    signals = relationship(
        "AISignal",
        back_populates="asset",
        lazy="selectin",
    )

    watchlist_items = relationship(
        "WatchlistItem",
        back_populates="asset",
        lazy="selectin",
    )


# ─────────────────────────────────────────────────────────────
# Watchlists
# ─────────────────────────────────────────────────────────────

class Watchlist(Base):

    __tablename__ = "watchlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # RELATIONSHIPS
    items = relationship(
        "WatchlistItem",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ─────────────────────────────────────────────────────────────
# Watchlist Items
# ─────────────────────────────────────────────────────────────

class WatchlistItem(Base):

    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id"),
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text
    )

    # RELATIONSHIPS
    watchlist = relationship(
        "Watchlist",
        back_populates="items",
        lazy="joined",
    )

    asset = relationship(
        "Asset",
        back_populates="watchlist_items",
        lazy="joined",
    )