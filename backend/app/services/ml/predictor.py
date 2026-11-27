import os
import joblib
import pandas as pd

from app.services.ml.feature_builder import FeatureBuilder


MODEL_PATH = "app/services/ml/models/random_forest.pkl"


class MLPredictor:

    def __init__(self):
        self.model = None
        self.builder = FeatureBuilder()
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)

    def predict(
        self,
        df: pd.DataFrame,
        symbol: str,
    ):
        if self.model is None:
            if not os.path.exists(MODEL_PATH):
                raise FileNotFoundError(f"Modelo ML no entrenado aún en {MODEL_PATH}")
            self.model = joblib.load(MODEL_PATH)

        features = self.builder.build_features(
            df,
            symbol=symbol,
        )

        X = [[
            features["rsi"],
            features["macd_hist"],
            features["atr"],
            features["bb_width"],
            features["trend_strength"],
            features["price_vs_ema50"],
            features["price_vs_ema200"],
            features["signals_count"],
        ]]

        prediction = self.model.predict(X)[0]
        probability = max(self.model.predict_proba(X)[0])

        return {
            "symbol": symbol,
            "prediction": "bullish" if prediction == 1 else "bearish",
            "confidence": round(probability * 100, 2),
            "features": features,
        }
