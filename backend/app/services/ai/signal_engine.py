"""
Motor de Generación de Señales IA.
Combina indicadores técnicos y gestión de riesgo para emitir recomendaciones estructuradas.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SignalResult:
    signal_type: str  # buy | sell | hold | watch | avoid
    strategy: str
    confidence: float
    risk_score: float
    reward_score: float
    expected_return: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    rationale: str
    technical_factors: dict[str, Any] = field(default_factory=dict)
    fundamental_factors: dict[str, Any] = field(default_factory=dict)
    sentiment_score: float = 0.0


class SignalEngine:
    """Evalúa TechnicalResult y precio actual para generar una señal operativa."""

    async def generate_signal(
        self,
        symbol: str,
        technical: Any,
        current_price: float,
    ) -> SignalResult:
        trend = getattr(technical, "trend", "neutral")
        strength = float(getattr(technical, "strength", 50.0) or 50.0)
        rsi = getattr(technical, "rsi_14", None)
        macd_hist = getattr(technical, "macd_hist", None)
        atr = float(getattr(technical, "atr_14", None) or (current_price * 0.02))
        detected_signals = list(getattr(technical, "signals", []) or [])

        score = strength
        reasons: list[str] = [f"Tendencia {trend} (fuerza {strength:.1f}/100)"]

        if rsi is not None:
            if rsi < 30:
                score += 15
                reasons.append(f"RSI en sobreventa ({rsi:.1f})")
            elif rsi > 70:
                score -= 15
                reasons.append(f"RSI en sobrecompra ({rsi:.1f})")

        if macd_hist is not None:
            if macd_hist > 0:
                score += 8
                reasons.append("Momentum MACD positivo")
            elif macd_hist < 0:
                score -= 8
                reasons.append("Momentum MACD negativo")

        confidence = max(0.0, min(100.0, round(score if trend == "bullish" else (100.0 - score if trend == "bearish" else 50.0), 2)))

        if trend == "bullish" and confidence >= 55:
            signal_type = "buy"
            strategy = "trend_momentum_long"
            stop_loss = float(getattr(technical, "stop_loss_suggestion", None) or (current_price - 1.5 * atr))
            tp1 = float(getattr(technical, "take_profit_suggestion", None) or (current_price + 2.5 * atr))
            tp2 = current_price + 4.0 * atr
        elif trend == "bearish" and confidence >= 55:
            signal_type = "sell"
            strategy = "trend_momentum_short"
            stop_loss = current_price + 1.5 * atr
            tp1 = max(0.01, current_price - 2.5 * atr)
            tp2 = max(0.01, current_price - 4.0 * atr)
        else:
            signal_type = "hold"
            strategy = "neutral_consolidation"
            stop_loss = max(0.01, current_price - 1.5 * atr)
            tp1 = current_price + 2.0 * atr
            tp2 = current_price + 3.0 * atr

        risk = max(abs(current_price - stop_loss), 1e-6)
        reward = abs(tp1 - current_price)
        risk_reward = round(reward / risk, 2)
        expected_return = round((reward / max(current_price, 1e-6)) * 100.0, 2)
        risk_score = round(min(100.0, (risk / max(current_price, 1e-6)) * 1000.0), 2)
        reward_score = round(min(100.0, risk_reward * 30.0), 2)

        return SignalResult(
            signal_type=signal_type,
            strategy=strategy,
            confidence=confidence,
            risk_score=risk_score,
            reward_score=reward_score,
            expected_return=expected_return,
            entry_price=round(current_price, 6),
            stop_loss=round(stop_loss, 6),
            take_profit_1=round(tp1, 6),
            take_profit_2=round(tp2, 6),
            risk_reward=risk_reward,
            rationale="; ".join(reasons),
            technical_factors={
                "trend": trend,
                "strength": strength,
                "rsi_14": rsi,
                "macd_hist": macd_hist,
                "atr_14": atr,
                "signals": detected_signals,
            },
            fundamental_factors={},
            sentiment_score=0.0,
        )
