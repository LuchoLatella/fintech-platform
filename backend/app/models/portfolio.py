"""
Modelos ORM: Portfolio, PortfolioPosition, PortfolioTransaction, PortfolioSnapshot
"""
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Date, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    portfolio_type: Mapped[str] = mapped_column(String(20), default="real")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    broker: Mapped[Optional[str]] = mapped_column(String(50))
    broker_account: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    cash_balance: Mapped[float] = mapped_column(Numeric(20, 4), default=0)

    positions: Mapped[list["PortfolioPosition"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )

    transactions: Mapped[list["PortfolioTransaction"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )

    snapshots: Mapped[list["PortfolioSnapshot"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )

    user: Mapped["User"] = relationship(
        back_populates="portfolios"
    )

class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"))
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    quantity: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    avg_cost: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    portfolio: Mapped["Portfolio"] = relationship(
        back_populates="positions"
    )

    asset: Mapped["Asset"] = relationship(
        lazy="joined"
    )

class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    fx_rate: Mapped[float] = mapped_column(Numeric(12, 6), default=1)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped["Portfolio"] = relationship(
    back_populates="transactions"
    )

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 4))
    total_value_ars: Mapped[Optional[float]] = mapped_column(Numeric(24, 2))
    daily_return: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    total_return: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    cash_balance: Mapped[Optional[float]] = mapped_column(Numeric(20, 4))
    positions_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB)

    portfolio: Mapped["Portfolio"] = relationship(
        back_populates="snapshots"
    )