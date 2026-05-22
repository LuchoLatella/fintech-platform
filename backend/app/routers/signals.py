"""
Router: Señales IA
Endpoints para obtener recomendaciones generadas por el motor de IA.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.routers.auth import get_current_user

router = APIRouter()


class SignalResponse(BaseModel):
    id: str
    symbol: str
    asset_name: str
    exchange: str
    asset_class: str
    signal_type: str
    strategy: str
    confidence: float
    risk_score: float
    expected_return: Optional[float]
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit_1: Optional[float]
    risk_reward: Optional[float]
    rationale: str
    technical_factors: dict
    fundamental_factors: dict
    sentiment_score: float
    generated_at: str


@router.get("/", summary="Señales activas del mercado")
async def get_active_signals(
    signal_type: Optional[str] = Query(None, description="buy | sell | watch | hold | avoid"),
    asset_class: Optional[str] = Query(None, description="stock | etf | cedear | crypto | bond"),
    min_confidence: float = Query(60, ge=0, le=100),
    limit: int = Query(20, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna las señales activas generadas por la IA, ordenadas por confianza.
    Filtros disponibles: tipo de señal, clase de activo, confianza mínima.
    """
    from app.models.signal import AISignal
    from app.models.asset import Asset, AssetClass, Exchange

    query = (
        select(AISignal, Asset, AssetClass, Exchange)
        .join(Asset, AISignal.asset_id == Asset.id)
        .join(AssetClass, Asset.asset_class_id == AssetClass.id)
        .join(Exchange, Asset.exchange_id == Exchange.id)
        .where(
            AISignal.is_active == True,
            AISignal.confidence >= min_confidence,
        )
    )

    if signal_type:
        query = query.where(AISignal.signal_type == signal_type)
    if asset_class:
        query = query.where(AssetClass.code == asset_class)

    query = query.order_by(AISignal.confidence.desc()).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return [
        SignalResponse(
            id=str(s.id),
            symbol=a.symbol,
            asset_name=a.name,
            exchange=e.code,
            asset_class=ac.code,
            signal_type=s.signal_type,
            strategy=s.strategy or "swing_trade",
            confidence=s.confidence,
            risk_score=s.risk_score or 50,
            expected_return=s.expected_return,
            entry_price=s.entry_price,
            stop_loss=s.stop_loss,
            take_profit_1=s.take_profit_1,
            risk_reward=s.risk_reward,
            rationale=s.rationale or "",
            technical_factors=s.technical_factors or {},
            fundamental_factors=s.fundamental_factors or {},
            sentiment_score=s.sentiment_score or 0,
            generated_at=str(s.generated_at),
        )
        for s, a, ac, e in rows
    ]


@router.get("/analyze/{symbol}", summary="Analizar un activo en tiempo real")
async def analyze_symbol(
    symbol: str,
    timeframe: str = Query("1d", description="1m | 5m | 15m | 1h | 4h | 1d | 1w"),
    current_user=Depends(get_current_user),
    redis=Depends(get_redis),
):
    """
    Análisis completo en tiempo real para un símbolo específico.
    Ejecuta el pipeline técnico + IA y retorna la señal con explicación.
    """
    from app.services.market_data.provider import MarketDataProvider
    from app.services.analysis.technical import TechnicalAnalysisEngine
    from app.services.ai.signal_engine import SignalEngine

    cache_key = f"analysis:{symbol}:{timeframe}"
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

    provider = MarketDataProvider(redis_client=redis)
    engine = TechnicalAnalysisEngine()
    signal_engine = SignalEngine()

    try:
        # Obtener datos
        ohlcv = await provider.get_ohlcv(symbol, timeframe)
        quote = await provider.get_quote(symbol)

        # Análisis técnico
        technical = engine.analyze(ohlcv.data, symbol, timeframe)

        # Generar señal IA
        signal = await signal_engine.generate_signal(
            symbol=symbol,
            technical=technical,
            current_price=quote.price,
        )

        result = {
            "symbol": symbol,
            "current_price": quote.price,
            "change_pct": quote.change_pct,
            "timeframe": timeframe,
            "signal": {
                "type": signal.signal_type,
                "strategy": signal.strategy,
                "confidence": signal.confidence,
                "risk_score": signal.risk_score,
                "expected_return": signal.expected_return,
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit_1": signal.take_profit_1,
                "take_profit_2": signal.take_profit_2,
                "risk_reward": signal.risk_reward,
                "rationale": signal.rationale,
            },
            "technical": {
                "trend": technical.trend,
                "strength": technical.strength,
                "rsi_14": technical.rsi_14,
                "macd_hist": technical.macd_hist,
                "bb_width": technical.bb_width,
                "atr_14": technical.atr_14,
                "signals": technical.signals,
                "ema_21": technical.ema_21,
                "ema_50": technical.ema_50,
                "ema_200": technical.ema_200,
            },
            "disclaimer": "Análisis informativo. No constituye asesoramiento financiero profesional.",
        }

        if redis:
            import json
            await redis.setex(cache_key, 120, json.dumps(result, default=str))

        return result

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error al analizar {symbol}: {str(e)}")
    finally:
        await provider.close()


@router.get("/ranking", summary="Ranking de mejores oportunidades")
async def get_opportunity_ranking(
    top: int = Query(10, le=50),
    market: Optional[str] = Query(None, description="ARG | US | CRYPTO"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Top N oportunidades de inversión detectadas, rankeadas por score combinado
    (confianza × reward / risk).
    """
    from app.models.signal import AISignal
    from app.models.asset import Asset, Exchange
    from sqlalchemy import func as sqlfunc

    query = (
        select(AISignal, Asset, Exchange)
        .join(Asset, AISignal.asset_id == Asset.id)
        .join(Exchange, Asset.exchange_id == Exchange.id)
        .where(AISignal.is_active == True, AISignal.signal_type == "buy", AISignal.confidence >= 65)
    )

    if market == "ARG":
        query = query.where(Exchange.country == "AR")
    elif market == "US":
        query = query.where(Exchange.country == "US")
    elif market == "CRYPTO":
        query = query.where(Exchange.code == "BINANCE")

    query = query.order_by(AISignal.confidence.desc()).limit(top)
    result = await db.execute(query)
    rows = result.all()

    return {
        "ranking": [
            {
                "rank": i + 1,
                "symbol": a.symbol,
                "name": a.name,
                "exchange": e.code,
                "signal_type": s.signal_type,
                "confidence": s.confidence,
                "risk_score": s.risk_score,
                "expected_return": s.expected_return,
                "risk_reward": s.risk_reward,
                "rationale": s.rationale,
                "entry_price": s.entry_price,
                "stop_loss": s.stop_loss,
                "take_profit": s.take_profit_1,
            }
            for i, (s, a, e) in enumerate(rows)
        ],
        "total": len(rows),
        "disclaimer": "Análisis informativo. No constituye asesoramiento financiero.",
    }