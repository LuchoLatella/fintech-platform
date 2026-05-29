"""
Router: Análisis Técnico y Fundamental
"""

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_redis
from app.services.market_data.provider import MarketDataProvider
from app.services.analysis.technical import (
    TechnicalAnalysisEngine,
)

router = APIRouter()


@router.get("/technical/{symbol}")
async def technical_analysis(
    symbol: str,
    timeframe: str = "1d",
    redis=Depends(get_redis),
):

    provider = MarketDataProvider(
        redis_client=redis
    )

    try:

        # HISTÓRICO
        ohlcv = await provider.get_ohlcv(
            symbol=symbol.upper(),
            timeframe=timeframe,
        )

        # ENGINE
        engine = TechnicalAnalysisEngine()

        result = engine.analyze(
            df=ohlcv.data,
            symbol=symbol.upper(),
            timeframe=timeframe,
        )

        return {
            "symbol": result.symbol,
            "timeframe": result.timeframe,

            "trend": result.trend,
            "strength": result.strength,

            "signals": result.signals,

            "rsi_14": result.rsi_14,

            "ema_9": result.ema_9,
            "ema_21": result.ema_21,
            "ema_50": result.ema_50,
            "ema_200": result.ema_200,

            "macd_line": result.macd_line,
            "macd_signal": result.macd_signal,
            "macd_hist": result.macd_hist,

            "bb_upper": result.bb_upper,
            "bb_middle": result.bb_middle,
            "bb_lower": result.bb_lower,

            "atr_14": result.atr_14,

            "vwap": result.vwap,

            "stop_loss":
                result.stop_loss_suggestion,

            "take_profit":
                result.take_profit_suggestion,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        await provider.close()