from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.models.signal import AISignal

from app.services.market_data.provider import (
    MarketDataProvider
)

from app.services.ml.predictor import (
    MLPredictor
)

router = APIRouter()

predictor = MLPredictor()


@router.get("/predict/{symbol}")
async def predict_asset(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):

    provider = MarketDataProvider()

    try:

        ohlcv = await provider.get_ohlcv(
            symbol=symbol,
            timeframe="1d",
        )

        result = predictor.predict(
            ohlcv.data,
            symbol=symbol,
        )

        signal = AISignal(
            asset_id=symbol,

            signal_type=result["prediction"],

            confidence=result["confidence"],

            rationale="Predicción ML automática",

            is_active=True,
        )

        db.add(signal)

        await db.commit()

        return {
            "ok": True,
            "data": result,
        }

    except Exception as e:

        return {
            "ok": False,
            "error": str(e),
        }

    finally:
        await provider.close()