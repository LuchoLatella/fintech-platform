import pandas as pd

from app.services.analysis.technical import TechnicalAnalysisEngine


class FeatureBuilder:

    def __init__(self):
        self.engine = TechnicalAnalysisEngine()

    def build_features(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
    ) -> dict:

        result = self.engine.analyze(
            df,
            symbol=symbol,
            timeframe=timeframe,
        )

        last_close = float(df["close"].iloc[-1])

        features = {
            "symbol": symbol,

            "close": last_close,

            "rsi": result.rsi_14 or 0,

            "macd_hist": result.macd_hist or 0,

            "ema_9": result.ema_9 or 0,
            "ema_21": result.ema_21 or 0,
            "ema_50": result.ema_50 or 0,
            "ema_200": result.ema_200 or 0,

            "atr": result.atr_14 or 0,

            "bb_width": result.bb_width or 0,

            "trend_strength": result.strength or 50,

            "bullish": 1 if result.trend == "bullish" else 0,

            "bearish": 1 if result.trend == "bearish" else 0,

            "signals_count": len(result.signals),

            "volume": float(df["volume"].iloc[-1]),

            "volume_avg_20": float(
                df["volume"].tail(20).mean()
            ),

            "price_vs_ema50":
                (
                    last_close - (result.ema_50 or last_close)
                ) / last_close,

            "price_vs_ema200":
                (
                    last_close - (result.ema_200 or last_close)
                ) / last_close,
        }

        return features