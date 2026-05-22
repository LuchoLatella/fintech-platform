"""
Router: Alertas
CRUD de reglas de alerta + historial de eventos disparados.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class AlertRuleCreate(BaseModel):
    asset_id: Optional[str] = None
    alert_name: str
    alert_type: str
    condition_value: Optional[float] = None
    condition_pct: Optional[float] = None
    timeframe: Optional[str] = "1d"
    channels: list[str] = ["email"]
    repeat: bool = False
    cooldown_minutes: int = 60

class AlertRuleResponse(BaseModel):
    id: str
    alert_name: str
    alert_type: str
    asset_id: Optional[str]
    condition_value: Optional[float]
    condition_pct: Optional[float]
    channels: list[str]
    is_active: bool
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/", summary="Listar mis alertas")
async def list_alerts(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.alert import AlertRule
    result = await db.execute(
        select(AlertRule).where(AlertRule.user_id == current_user.id).order_by(AlertRule.created_at.desc())
    )
    rules = result.scalars().all()
    return [
        AlertRuleResponse(
            id=str(r.id), alert_name=r.alert_name, alert_type=r.alert_type,
            asset_id=str(r.asset_id) if r.asset_id else None,
            condition_value=r.condition_value, condition_pct=r.condition_pct,
            channels=r.channels or [], is_active=r.is_active,
            created_at=str(r.created_at),
        ) for r in rules
    ]


@router.post("/", status_code=201, summary="Crear nueva alerta")
async def create_alert(
    data: AlertRuleCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.alert import AlertRule

    # Límite de alertas por plan
    plan_limits = {"free": 5, "pro": 50, "enterprise": 500}
    limit = plan_limits.get(current_user.plan, 5)
    count_result = await db.execute(
        select(AlertRule).where(AlertRule.user_id == current_user.id, AlertRule.is_active == True)
    )
    if len(count_result.scalars().all()) >= limit:
        raise HTTPException(status_code=403, detail=f"Límite de {limit} alertas activas para plan {current_user.plan}")

    rule = AlertRule(
        user_id=current_user.id,
        asset_id=uuid.UUID(data.asset_id) if data.asset_id else None,
        alert_name=data.alert_name,
        alert_type=data.alert_type,
        condition_value=data.condition_value,
        condition_pct=data.condition_pct,
        timeframe=data.timeframe,
        channels=data.channels,
        repeat=data.repeat,
        cooldown_minutes=data.cooldown_minutes,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": str(rule.id), "message": "Alerta creada exitosamente"}


@router.delete("/{alert_id}", summary="Eliminar alerta")
async def delete_alert(
    alert_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.alert import AlertRule
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == uuid.UUID(alert_id), AlertRule.user_id == current_user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    await db.delete(rule)
    await db.commit()
    return {"message": "Alerta eliminada"}


@router.get("/events", summary="Historial de alertas disparadas")
async def get_alert_events(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.alert import AlertRule, AlertEvent
    result = await db.execute(
        select(AlertEvent)
        .join(AlertRule, AlertEvent.rule_id == AlertRule.id)
        .where(AlertRule.user_id == current_user.id)
        .order_by(AlertEvent.triggered_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "rule_id": str(e.rule_id),
            "message": e.message,
            "triggered_value": e.triggered_value,
            "channels_sent": e.channels_sent,
            "was_delivered": e.was_delivered,
            "triggered_at": str(e.triggered_at),
        } for e in events
    ]