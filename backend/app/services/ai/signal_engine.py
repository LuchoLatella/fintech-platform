"""
Worker: Alert Checker
Celery task que se ejecuta cada 60 segundos y evalúa todas las alertas activas.
"""
from datetime import datetime, timedelta
from typing import Optional

import structlog
from celery import shared_task
from sqlalchemy import select

log = structlog.get_logger()


@shared_task(name="app.workers.alert_checker.check_all_alerts", bind=True, max_retries=3)
def check_all_alerts(self):
    """
    Task principal: verifica todas las reglas de alerta activas.
    Se ejecuta sincrónicamente (Celery no soporta async nativamente).
    """
    import asyncio
    try:
        asyncio.get_event_loop().run_until_complete(_check_all_alerts_async())
    except Exception as exc:
        log.error("alert_checker_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


async def _check_all_alerts_async():
    """Versión async del checker."""
    from app.database import AsyncSessionLocal
    from app.models.alert import AlertRule, AlertEvent
    from app.services.notifications.telegram import TelegramService, EmailService

    telegram = TelegramService()
    email_svc = EmailService()

    async with AsyncSessionLocal() as db:
        # Obtener todas las alertas activas
        result = await db.execute(
            select(AlertRule).where(AlertRule.is_active == True)
        )
        rules = result.scalars().all()
        log.info("checking_alerts", total=len(rules))

        for rule in rules:
            try:
                # Verificar cooldown
                if rule.last_triggered_at:
                    cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
                    if datetime.utcnow() < cooldown_end:
                        continue

                triggered, value, message = await evaluate_rule(rule)

                if triggered:
                    # Registrar evento
                    event = AlertEvent(
                        rule_id=rule.id,
                        asset_id=rule.asset_id,
                        triggered_value=value,
                        message=message,
                        channels_sent=rule.channels or [],
                        was_delivered=False,
                    )
                    db.add(event)

                    # Actualizar última activación
                    rule.last_triggered_at = datetime.utcnow()
                    if not rule.repeat:
                        rule.is_active = False

                    # Enviar notificaciones
                    delivered = await dispatch_notifications(
                        rule=rule, message=message,
                        telegram=telegram, email_svc=email_svc,
                        db=db
                    )
                    event.was_delivered = delivered
                    await db.commit()
                    log.info("alert_triggered", rule_id=str(rule.id), asset_id=str(rule.asset_id))

            except Exception as e:
                log.error("rule_check_failed", rule_id=str(rule.id), error=str(e))
                continue

    await telegram.close()
    await email_svc.close()


async def evaluate_rule(rule) -> tuple[bool, Optional[float], str]:
    """
    Evalúa si una regla de alerta se cumple.
    Retorna (triggered, valor_actual, mensaje).
    """
    from app.database import AsyncSessionLocal
    from app.services.market_data.provider import MarketDataProvider

    if not rule.asset_id:
        return await evaluate_global_rule(rule)

    provider = MarketDataProvider()
    try:
        quote = await provider.get_quote(str(rule.asset_id))
        price = quote.price

        match rule.alert_type:
            case "price_above":
                if price >= rule.condition_value:
                    return True, price, f"Precio {price:.4f} superó el nivel {rule.condition_value:.4f}"

            case "price_below":
                if price <= rule.condition_value:
                    return True, price, f"Precio {price:.4f} cayó por debajo de {rule.condition_value:.4f}"

            case "price_change_pct":
                if quote.change_pct and abs(quote.change_pct) >= rule.condition_pct:
                    direction = "subió" if quote.change_pct > 0 else "cayó"
                    return True, price, f"Precio {direction} {abs(quote.change_pct):.2f}% (umbral: {rule.condition_pct:.2f}%)"

            case "volume_spike":
                # Implementar comparación con volumen promedio
                pass

            case "rsi_oversold" | "rsi_overbought" | "macd_cross_bullish" | "macd_cross_bearish" | "bb_breakout":
                return await evaluate_technical_rule(rule, price)

            case "ai_signal":
                return await evaluate_ai_signal_rule(rule)

        return False, None, ""
    finally:
        await provider.close()


async def evaluate_global_rule(rule) -> tuple[bool, Optional[float], str]:
    """Evalúa alertas que no están asociadas a un activo específico."""
    from app.services.argentina.dolar import ArgentinaService

    if rule.alert_type == "arg_dolar_change":
        svc = ArgentinaService()
        try:
            rates = await svc.get_dolar_rates()
            if rates.mep and rule.condition_pct:
                # Comparar con valor anterior en Redis (simplificado)
                return False, rates.mep, ""
        finally:
            await svc.close()

    if rule.alert_type == "arg_riesgo_pais":
        svc = ArgentinaService()
        try:
            rp = await svc.get_riesgo_pais()
            if rp.value >= rule.condition_value:
                return True, rp.value, f"Riesgo país alcanzó {rp.value:.0f} bps (umbral: {rule.condition_value:.0f})"
        finally:
            await svc.close()

    return False, None, ""


async def evaluate_technical_rule(rule, current_price: float) -> tuple[bool, Optional[float], str]:
    """Evalúa señales técnicas (RSI, MACD, BB) para una alerta."""
    from app.services.market_data.provider import MarketDataProvider
    from app.services.analysis.technical import TechnicalAnalysisEngine

    provider = MarketDataProvider()
    engine = TechnicalAnalysisEngine()
    try:
        ohlcv = await provider.get_ohlcv(str(rule.asset_id), rule.timeframe or "1d")
        result = engine.analyze(ohlcv.data, str(rule.asset_id), rule.timeframe or "1d")

        match rule.alert_type:
            case "rsi_oversold":
                if result.rsi_14 and result.rsi_14 < 30:
                    return True, result.rsi_14, f"RSI en zona de sobreventa: {result.rsi_14:.1f}"
            case "rsi_overbought":
                if result.rsi_14 and result.rsi_14 > 70:
                    return True, result.rsi_14, f"RSI en zona de sobrecompra: {result.rsi_14:.1f}"
            case "macd_cross_bullish":
                if "macd_bullish" in result.signals:
                    return True, current_price, "Cruce alcista del MACD detectado"
            case "macd_cross_bearish":
                if "macd_bearish" in result.signals:
                    return True, current_price, "Cruce bajista del MACD detectado"
            case "bb_breakout":
                if "bb_breakout_upper" in result.signals:
                    return True, current_price, "Ruptura alcista de Bollinger Band superior"
                if "bb_breakout_lower" in result.signals:
                    return True, current_price, "Ruptura bajista de Bollinger Band inferior"

        return False, None, ""
    finally:
        await provider.close()


async def evaluate_ai_signal_rule(rule) -> tuple[bool, Optional[float], str]:
    """Verifica si la IA generó una señal nueva para el activo."""
    from app.database import AsyncSessionLocal
    from app.models.signal import AISignal
    from sqlalchemy import and_

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AISignal).where(
                and_(
                    AISignal.asset_id == rule.asset_id,
                    AISignal.is_active == True,
                    AISignal.confidence >= (rule.condition_value or 70),
                    AISignal.generated_at > (datetime.utcnow() - timedelta(minutes=15)),
                )
            ).order_by(AISignal.confidence.desc()).limit(1)
        )
        signal = result.scalar_one_or_none()
        if signal:
            return (
                True,
                signal.confidence,
                f"Señal IA: {signal.signal_type.upper()} | Confianza {signal.confidence:.0f}% | {signal.rationale or ''}"
            )
    return False, None, ""


async def dispatch_notifications(rule, message: str, telegram, email_svc, db) -> bool:
    """Envía la alerta por los canales configurados en la regla."""
    from app.models.user import User, UserPreferences
    from sqlalchemy import select

    result = await db.execute(
        select(User, UserPreferences)
        .join(UserPreferences, User.id == UserPreferences.user_id)
        .where(User.id == rule.user_id)
    )
    row = result.first()
    if not row:
        return False

    user, prefs = row
    delivered = False

    channels = rule.channels or []

    if "telegram" in channels and prefs.telegram_chat_id:
        ok = await telegram.send_alert(
            chat_id=prefs.telegram_chat_id,
            alert_message=message,
            signal_type="buy" if "compra" in message.lower() or "alcista" in message.lower() else "sell",
        )
        if ok:
            delivered = True

    if "email" in channels and prefs.notification_email:
        ok = await email_svc.send_alert_email(
            to_email=user.email,
            alert_message=message,
        )
        if ok:
            delivered = True

    return delivered