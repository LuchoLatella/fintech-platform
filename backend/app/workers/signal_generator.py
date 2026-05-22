"""
Worker: Signal Generator
Task Celery que recorre todos los activos del watchlist global
y genera señales IA actualizadas cada 10 minutos.
"""
import asyncio
from datetime import datetime, timedelta

import structlog
from celery import shared_task

log = structlog.get_logger()


@shared_task(name="app.workers.signal_generator.generate_signals", bind=True, max_retries=2)
def generate_signals(self):
    """Genera señales para todos los activos activos del sistema."""
    try:
        asyncio.get_event_loop().run_until_complete(_generate_signals_async())
    except Exception as exc:
        log.error("signal_generator_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="app.workers.signal_generator.cleanup_expired_signals")
def cleanup_expired_signals():
    """Invalida señales vencidas o superadas por el mercado."""
    asyncio.get_event_loop().run_until_complete(_cleanup_async())


async def _generate_signals_async():
    from app.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.signal import AISignal
    from app.services.market_data.provider import MarketDataProvider
    from app.services.analysis.technical import TechnicalAnalysisEngine
    from app.services.ai.signal_engine import SignalEngine
    from sqlalchemy import select

    engine = TechnicalAnalysisEngine()
    signal_engine = SignalEngine()
    provider = MarketDataProvider()

    async with AsyncSessionLocal() as db:
        # Obtener activos activos para análisis
        result = await db.execute(
            select(Asset).where(Asset.is_active == True).limit(200)
        )
        assets = result.scalars().all()
        log.info("generating_signals", asset_count=len(assets))

        generated = 0
        for asset in assets:
            try:
                symbol = asset.symbol
                ohlcv = await provider.get_ohlcv(symbol, "1d")
                if ohlcv.data.empty or len(ohlcv.data) < 50:
                    continue

                quote = await provider.get_quote(symbol)
                technical = engine.analyze(ohlcv.data, symbol, "1d")
                signal = await signal_engine.generate_signal(
                    symbol=symbol,
                    technical=technical,
                    current_price=quote.price,
                )

                # Solo guardar señales con confianza mínima
                if signal.confidence < 55:
                    continue

                # Invalidar señal anterior del mismo activo
                from sqlalchemy import update
                await db.execute(
                    update(AISignal)
                    .where(AISignal.asset_id == asset.id, AISignal.is_active == True)
                    .values(is_active=False, invalidated_at=datetime.utcnow(),
                            invalidation_reason="superseded_by_new_signal")
                )

                # Crear nueva señal
                new_signal = AISignal(
                    asset_id=asset.id,
                    signal_type=signal.signal_type,
                    strategy=signal.strategy,
                    confidence=signal.confidence,
                    risk_score=signal.risk_score,
                    reward_score=signal.reward_score,
                    expected_return=signal.expected_return,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    take_profit_1=signal.take_profit_1,
                    take_profit_2=signal.take_profit_2,
                    risk_reward=signal.risk_reward,
                    rationale=signal.rationale,
                    technical_factors=signal.technical_factors,
                    fundamental_factors=signal.fundamental_factors,
                    sentiment_score=signal.sentiment_score,
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                )
                db.add(new_signal)
                generated += 1

            except Exception as e:
                log.warning("signal_failed", symbol=asset.symbol, error=str(e))
                continue

        await db.commit()
        log.info("signals_generated", count=generated)

    await provider.close()


async def _cleanup_async():
    from app.database import AsyncSessionLocal
    from app.models.signal import AISignal
    from sqlalchemy import update

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(AISignal)
            .where(
                AISignal.is_active == True,
                AISignal.expires_at < datetime.utcnow(),
            )
            .values(is_active=False, invalidated_at=datetime.utcnow(),
                    invalidation_reason="expired")
        )
        await db.commit()
        log.info("expired_signals_cleaned", count=result.rowcount)