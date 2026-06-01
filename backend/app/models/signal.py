"""
Modelos ORM: AISignal, AIModel
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    signals = relationship(
        "AISignal",
        back_populates="model",
    )

class AISignal(Base):

    __tablename__ = "ai_signals"

    __table_args__ = (

    Index(
        "ix_ai_signal_symbol_generated",
        "symbol",
        "generated_at",
    ),

    Index(
        "ix_ai_signal_active",
        "is_active",
    ),

    Index(
        "ix_ai_signal_confidence",
        "confidence",
    ),

    Index(
        "ix_ai_signal_scanner_rank",
        "scanner_rank",
    ),

    Index(
        "ix_ai_signal_active_confidence",
        "is_active",
        "confidence",
    ),
)

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id"),
    )

    model_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("ai_models.id"),
        nullable=True,
    )

    # ─────────────────────────────────────────────
    # Identificación
    # ─────────────────────────────────────────────

    symbol: Mapped[Optional[str]] = mapped_column(
        String(30),
        index=True,
    )

    exchange: Mapped[Optional[str]] = mapped_column(
        String(20)
    )

    timeframe: Mapped[Optional[str]] = mapped_column(
        String(5)
    )

    scanner_source: Mapped[Optional[str]] = mapped_column(
        String(30)
    )

    scanner_rank: Mapped[Optional[int]] = mapped_column(
        Integer
    )

    # ─────────────────────────────────────────────
    # Señal IA
    # ─────────────────────────────────────────────

    signal_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    strategy: Mapped[Optional[str]] = mapped_column(
        String(30)
    )

    trend: Mapped[Optional[str]] = mapped_column(
        String(20)
    )

    market_regime: Mapped[Optional[str]] = mapped_column(
        String(20)
    )

    confidence: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    ml_probability_bull: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2)
    )

    ml_probability_bear: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2)
    )

    # ─────────────────────────────────────────────
    # Riesgo / Reward
    # ─────────────────────────────────────────────

    risk_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2)
    )

    reward_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2)
    )

    expected_return: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 4)
    )

    risk_reward: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 4)
    )

    # ─────────────────────────────────────────────
    # Operación sugerida
    # ─────────────────────────────────────────────

    entry_price: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6)
    )

    stop_loss: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6)
    )

    take_profit_1: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6)
    )

    take_profit_2: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6)
    )

    # ─────────────────────────────────────────────
    # Explicabilidad IA
    # ─────────────────────────────────────────────

    rationale: Mapped[Optional[str]] = mapped_column(
        Text
    )

    technical_factors: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )

    fundamental_factors: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )

    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2)
    )

    # ─────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    invalidated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    invalidation_reason: Mapped[Optional[str]] = mapped_column(
        Text
    )

    # ─────────────────────────────────────────────
    # Tracking performance real
    # ─────────────────────────────────────────────

    is_executed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    execution_price: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6)
    )

    pnl_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4)
    )

    backtest_id: Mapped[Optional[str]] = mapped_column(
        String(50)
    )

    # ─────────────────────────────────────────────
    # RELATIONSHIPS
    # ─────────────────────────────────────────────

    asset = relationship(
        "Asset",
        back_populates="signals",
        lazy="joined",
    )

    model = relationship(
        "AIModel",
        back_populates="signals",
        lazy="joined",
    )