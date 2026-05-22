"""
Modelos ORM: AlertRule, AlertEvent
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, Numeric, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    alert_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    condition_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    timeframe: Mapped[Optional[str]] = mapped_column(String(5))
    channels: Mapped[Optional[list]] = mapped_column(ARRAY(Text), default=["email"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    events: Mapped[list["AlertEvent"]] = relationship(back_populates="rule", cascade="all, delete-orphan")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_rules.id"))
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    triggered_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channels_sent: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    was_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_errors: Mapped[Optional[dict]] = mapped_column(JSONB)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rule: Mapped["AlertRule"] = relationship(back_populates="events")