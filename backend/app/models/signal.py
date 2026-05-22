"""
Modelos ORM: AISignal, AIModel
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_type: Mapped[Optional[str]] = mapped_column(String(50))
    asset_class: Mapped[Optional[str]] = mapped_column(String(30))
    timeframe: Mapped[Optional[str]] = mapped_column(String(5))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Numeric(6, 4))
    sharpe_backtest: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    trained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AISignal(Base):
    __tablename__ = "ai_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    model_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ai_models.id"), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy: Mapped[Optional[str]] = mapped_column(String(30))
    timeframe: Mapped[Optional[str]] = mapped_column(String(5))
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    reward_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    expected_return: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    entry_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    stop_loss: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    take_profit_1: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    take_profit_2: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    risk_reward: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    technical_factors: Mapped[Optional[dict]] = mapped_column(JSONB)
    fundamental_factors: Mapped[Optional[dict]] = mapped_column(JSONB)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    invalidation_reason: Mapped[Optional[str]] = mapped_column(Text)