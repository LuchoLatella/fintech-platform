import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


MODEL_PATH = "app/services/ml/models/random_forest.pkl"


def train_model(dataset_path: str):

    df = pd.read_csv(dataset_path)

    feature_columns = [
        "rsi",
        "macd_hist",
        "atr",
        "bb_width",
        "trend_strength",
        "price_vs_ema50",
        "price_vs_ema200",
        "signals_count",
    ]

    X = df[feature_columns]

    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print(classification_report(
        y_test,
        predictions,
    ))

    joblib.dump(model, MODEL_PATH)

    print(f"Modelo guardado en {MODEL_PATH}")