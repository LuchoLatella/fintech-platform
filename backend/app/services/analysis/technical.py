"""
Motor de Análisis Técnico.
Calcula indicadores, detecta señales y genera un score de tendencia.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import pandas_ta as ta
import numpy as np

import structlog
log = structlog.get_logger()


@dataclass
class TechnicalResult:
    symbol: str
    timeframe: str
    # Tendencia
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    # Momentum
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    # Volatilidad
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    atr_14: Optional[float] = None
    # Volumen
    vwap: Optional[float] = None
    # Señales detectadas
    signals: list[str] = field(default_factory=list)
    trend: str = "neutral"       # bullish | bearish | neutral | sideways
    strength: float = 50.0       # 0-100: intensidad de la tendencia
    # Gestión de riesgo sugerida
    stop_loss_suggestion: Optional[float] = None
    take_profit_suggestion: Optional[float] = None


class TechnicalAnalysisEngine:
    """
    Calcula indicadores técnicos sobre un DataFrame OHLCV y
    detecta patrones y señales automáticamente.
    """

    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    BB_SQUEEZE_THRESHOLD = 0.05   # BB width < 5%: compresión de volatilidad

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str = "1d") -> TechnicalResult:
        """
        Entrada: DataFrame con columnas [time, open, high, low, close, volume]
        Salida: TechnicalResult con todos los indicadores y señales detectadas.
        """
        if len(df) < 50:
            log.warning("insufficient_data", symbol=symbol, rows=len(df))
            return TechnicalResult(symbol=symbol, timeframe=timeframe)

        df = df.copy().sort_values("time").reset_index(drop=True)
        result = TechnicalResult(symbol=symbol, timeframe=timeframe)

        self._calculate_moving_averages(df, result)
        self._calculate_momentum(df, result)
        self._calculate_volatility(df, result)
        self._calculate_volume(df, result)
        self._detect_signals(df, result)
        self._calculate_trend_strength(result)
        self._suggest_risk_levels(df, result)

        return result

    def _calculate_moving_averages(self, df: pd.DataFrame, result: TechnicalResult):
        close = df["close"]
        result.ema_9   = self._last(ta.ema(close, length=9))
        result.ema_21  = self._last(ta.ema(close, length=21))
        result.ema_50  = self._last(ta.ema(close, length=50))
        result.ema_200 = self._last(ta.ema(close, length=200))
        result.sma_20  = self._last(ta.sma(close, length=20))
        result.sma_50  = self._last(ta.sma(close, length=50))
        result.sma_200 = self._last(ta.sma(close, length=200))

    def _calculate_momentum(self, df: pd.DataFrame, result: TechnicalResult):
        close = df["close"]
        # RSI
        rsi = ta.rsi(close, length=14)
        result.rsi_14 = self._last(rsi)

        # MACD
        macd = ta.macd(close, fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            result.macd_line   = self._last(macd.iloc[:, 0])
            result.macd_signal = self._last(macd.iloc[:, 2])
            result.macd_hist   = self._last(macd.iloc[:, 1])

        # Estocástico
        stoch = ta.stoch(df["high"], df["low"], close, k=14, d=3)
        if stoch is not None and not stoch.empty:
            result.stoch_k = self._last(stoch.iloc[:, 0])
            result.stoch_d = self._last(stoch.iloc[:, 1])

    def _calculate_volatility(self, df: pd.DataFrame, result: TechnicalResult):
        close = df["close"]
        # Bollinger Bands
        bb = ta.bbands(close, length=20, std=2)
        if bb is not None and not bb.empty:
            result.bb_lower  = self._last(bb.iloc[:, 0])
            result.bb_middle = self._last(bb.iloc[:, 1])
            result.bb_upper  = self._last(bb.iloc[:, 2])
            if result.bb_middle and result.bb_middle > 0:
                result.bb_width = (result.bb_upper - result.bb_lower) / result.bb_middle

        # ATR
        result.atr_14 = self._last(ta.atr(df["high"], df["low"], close, length=14))

    def _calculate_volume(self, df: pd.DataFrame, result: TechnicalResult):
        if "volume" in df.columns and df["volume"].sum() > 0:
            result.vwap = self._last(ta.vwap(df["high"], df["low"], df["close"], df["volume"]))

    def _detect_signals(self, df: pd.DataFrame, result: TechnicalResult):
        signals = []
        close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2] if len(df) > 1 else close

        # ── RSI ───────────────────────────────────────────────────────────────
        if result.rsi_14:
            if result.rsi_14 < self.RSI_OVERSOLD:
                signals.append("rsi_oversold")
            elif result.rsi_14 > self.RSI_OVERBOUGHT:
                signals.append("rsi_overbought")
            elif 40 <= result.rsi_14 <= 60:
                signals.append("rsi_neutral")

        # ── MACD ──────────────────────────────────────────────────────────────
        if result.macd_hist is not None:
            prev_hist = df["close"].apply(lambda x: x).iloc[-2] if len(df) > 2 else None
            if result.macd_line and result.macd_signal:
                if result.macd_line > result.macd_signal and result.macd_hist > 0:
                    signals.append("macd_bullish")
                elif result.macd_line < result.macd_signal and result.macd_hist < 0:
                    signals.append("macd_bearish")

        # ── Precio vs EMAs ────────────────────────────────────────────────────
        if result.ema_50 and result.ema_200:
            if result.ema_50 > result.ema_200:
                signals.append("golden_cross_setup")  # EMA50 sobre EMA200 = tendencia alcista
            else:
                signals.append("death_cross_setup")

        if result.ema_21 and close > result.ema_21:
            signals.append("price_above_ema21")
        if result.ema_50 and close > result.ema_50:
            signals.append("price_above_ema50")
        if result.ema_200 and close > result.ema_200:
            signals.append("price_above_ema200")

        # ── Bollinger Bands ───────────────────────────────────────────────────
        if result.bb_upper and result.bb_lower and result.bb_middle:
            if close > result.bb_upper:
                signals.append("bb_breakout_upper")
            elif close < result.bb_lower:
                signals.append("bb_breakout_lower")
            if result.bb_width and result.bb_width < self.BB_SQUEEZE_THRESHOLD:
                signals.append("bb_squeeze")  # compresión: volatilidad baja, expansión inminente

        # ── Sobrecompra / sobreventa combinada ────────────────────────────────
        if "rsi_oversold" in signals and result.macd_hist and result.macd_hist > 0:
            signals.append("strong_oversold_reversal")
        if "rsi_overbought" in signals and result.macd_hist and result.macd_hist < 0:
            signals.append("strong_overbought_reversal")

        # ── Volumen ────────────────────────────────────────────────────────────
        if "volume" in df.columns and len(df) > 20:
            avg_vol = df["volume"].tail(20).mean()
            last_vol = df["volume"].iloc[-1]
            if avg_vol > 0 and last_vol > avg_vol * 2:
                signals.append("volume_spike")

        result.signals = signals

    def _calculate_trend_strength(self, result: TechnicalResult):
        """
        Asigna una puntuación de tendencia (0-100) y etiqueta bullish/bearish/neutral.
        """
        score = 50  # neutro
        bullish_points = 0
        bearish_points = 0

        # RSI
        if result.rsi_14:
            if result.rsi_14 > 50: bullish_points += 10
            else: bearish_points += 10

        # MACD
        if "macd_bullish" in result.signals: bullish_points += 15
        if "macd_bearish" in result.signals: bearish_points += 15

        # EMAs
        if "price_above_ema21" in result.signals: bullish_points += 10
        if "price_above_ema50" in result.signals: bullish_points += 15
        if "price_above_ema200" in result.signals: bullish_points += 20
        if "golden_cross_setup" in result.signals: bullish_points += 10
        if "death_cross_setup" in result.signals: bearish_points += 10

        total = bullish_points + bearish_points
        if total > 0:
            score = 50 + (bullish_points - bearish_points) / total * 50

        result.strength = round(min(max(score, 0), 100), 1)

        if result.strength >= 65:
            result.trend = "bullish"
        elif result.strength <= 35:
            result.trend = "bearish"
        elif 45 <= result.strength <= 55:
            result.trend = "sideways"
        else:
            result.trend = "neutral"

    def _suggest_risk_levels(self, df: pd.DataFrame, result: TechnicalResult):
        """
        Sugiere stop loss y take profit basados en ATR y soportes/resistencias.
        """
        if not result.atr_14:
            return
        close = df["close"].iloc[-1]
        atr = result.atr_14

        if result.trend == "bullish":
            result.stop_loss_suggestion = round(close - 2 * atr, 4)
            result.take_profit_suggestion = round(close + 3 * atr, 4)
        elif result.trend == "bearish":
            result.stop_loss_suggestion = round(close + 2 * atr, 4)
            result.take_profit_suggestion = round(close - 3 * atr, 4)

    @staticmethod
    def _last(series) -> Optional[float]:
        """Retorna el último valor no-NaN de una Serie."""
        if series is None or len(series) == 0:
            return None
        val = series.dropna().iloc[-1] if not series.dropna().empty else None
        return round(float(val), 6) if val is not None else None