"""
Indicators Module

Contiene la clase TechnicalIndicators encargada de calcular
indicadores técnicos básicos sobre un DataFrame de precios.

Autor: FinTech Platform
"""

from __future__ import annotations

import pandas as pd
import numpy as np


class TechnicalIndicators:

    REQUIRED_COLUMNS = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    def __init__(self, df: pd.DataFrame):

        if df is None or df.empty:
            raise ValueError("El DataFrame recibido está vacío.")

        self.df = df.copy()

        self._normalize_columns()

        self._validate_dataframe()

    # --------------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------------

    def _normalize_columns(self):

        self.df.columns = [str(c).strip().title() for c in self.df.columns]

    def _validate_dataframe(self):

        missing = [
            c for c in self.REQUIRED_COLUMNS
            if c not in self.df.columns
        ]

        if missing:
            raise ValueError(
                f"Faltan columnas requeridas: {missing}"
            )

    # --------------------------------------------------------
    # MOVING AVERAGES
    # --------------------------------------------------------

    def sma(self, period: int):

        self.df[f"SMA_{period}"] = (
            self.df["Close"]
            .rolling(period)
            .mean()
        )

        return self.df

    def ema(self, period: int):

        self.df[f"EMA_{period}"] = (
            self.df["Close"]
            .ewm(
                span=period,
                adjust=False
            )
            .mean()
        )

        return self.df

    def wma(self, period: int):

        weights = np.arange(1, period + 1)

        self.df[f"WMA_{period}"] = (
            self.df["Close"]
            .rolling(period)
            .apply(
                lambda prices:
                np.dot(prices, weights) / weights.sum(),
                raw=True
            )
        )

        return self.df

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def add_basic_moving_averages(self):

        periods = [
            5,
            10,
            20,
            50,
            100,
            200
        ]

        for p in periods:

            self.sma(p)
            self.ema(p)

        return self.df

    def dataframe(self):

        return self.df