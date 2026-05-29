import joblib
import pandas as pd

from app.services.ml.feature_builder import FeatureBuilder


MODEL_PATH = "app/services/ml/models/random_forest.pkl"


class MLPredictor:

    def __init__(self):

        self.model = joblib.load(MODEL_PATH)

        self.builder = FeatureBuilder()

    def predict(
        self,
        df: pd.DataFrame,
        symbol: str,
    ):

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

        probability = max(
            self.model.predict_proba(X)[0]
        )

        return {
            "symbol": symbol,

            "prediction":
                "bullish"
                if prediction == 1
                else "bearish",

            "confidence":
                round(probability * 100, 2),

            "features": features,
        }