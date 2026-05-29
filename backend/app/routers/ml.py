from fastapi import APIRouter

from app.services.market_data.provider import MarketDataProvider
from app.services.ml.predictor import MLPredictor

router = APIRouter()

predictor = MLPredictor()


@router.get("/predict/{symbol}")
async def predict_symbol(symbol: str):

    provider = MarketDataProvider()

    try:

        ohlcv = await provider.get_ohlcv(
            symbol=symbol,
            timeframe="1d",
        )

        result = predictor.predict(
            ohlcv.data,
            symbol,
        )

        return result

    finally:
        await provider.close()