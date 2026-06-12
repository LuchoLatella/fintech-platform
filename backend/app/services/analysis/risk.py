"""
Risk Service — Cálculo de métricas de riesgo de portafolio.
VaR, CVaR, Sharpe, Sortino, Beta, Max Drawdown, diversificación.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd

import structlog
log = structlog.get_logger()


@dataclass
class RiskMetrics:
    # VaR
    var_95_1d: Optional[float] = None
    var_99_1d: Optional[float] = None
    cvar_95_1d: Optional[float] = None
    # Rendimiento ajustado por riesgo
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    # Volatilidad
    volatility_daily: Optional[float] = None
    volatility_annual: Optional[float] = None
    # Drawdown
    max_drawdown: Optional[float] = None
    current_drawdown: Optional[float] = None
    # Mercado
    beta: Optional[float] = None
    alpha: Optional[float] = None
    # Concentración
    top1_concentration: Optional[float] = None
    top5_concentration: Optional[float] = None
    diversification_score: Optional[float] = None
    sector_concentration: dict = None
    avg_correlation: Optional[float] = None
    # Resumen
    risk_label: str = "moderate"   # low | moderate | high | critical


class RiskService:
    """
    Calcula métricas de riesgo para un portafolio dado.
    Recibe retornos históricos diarios de cada posición.
    """

    TRADING_DAYS = 252
    RISK_FREE_RATE = 0.05   # 5% anual (ajustar según tasa BCRA o treasury)

    def calculate_portfolio_risk(
        self,
        returns_df: pd.DataFrame,       # columnas = símbolos, filas = fechas, valores = retornos diarios
        weights: dict[str, float],      # {símbolo: peso en portafolio 0-1}
        benchmark_returns: Optional[pd.Series] = None,  # retornos del benchmark (S&P500 o Merval)
        positions_by_sector: Optional[dict] = None,
    
    ) -> RiskMetrics:
        """
        Calcula todas las métricas de riesgo del portafolio.
        """
        print("=" * 80)
        print("RETURNS_DF")
        print(returns_df.head())
        print("ROWS:", len(returns_df))
        print("COLS:", returns_df.columns.tolist())

        print("=" * 80)
        print("WEIGHTS")
        print(weights)
        print("=" * 80)

        metrics = RiskMetrics()

        if returns_df.empty or not weights:
            return metrics

        # Alinear columnas con weights
        symbols = [s for s in weights if s in returns_df.columns]
        print("SYMBOLS ENCONTRADOS:", symbols)
        if not symbols:
            return metrics

        df = returns_df[symbols].dropna()
        w = np.array([weights[s] for s in symbols])
        w = w / w.sum()   # normalizar

        # Retornos del portafolio
        portfolio_returns = df.values @ w

        print("PORTFOLIO RETURNS")
        print(portfolio_returns[:10])
        print("CANTIDAD RETURNS:", len(portfolio_returns))

        # ── VaR ────────────────────────────────────────────────────────────────
        metrics.var_95_1d = self._var(portfolio_returns, 0.95)
        metrics.var_99_1d = self._var(portfolio_returns, 0.99)
        metrics.cvar_95_1d = self._cvar(portfolio_returns, 0.95)

        # ── Volatilidad ────────────────────────────────────────────────────────
        metrics.volatility_daily = float(np.std(portfolio_returns))
        metrics.volatility_annual = metrics.volatility_daily * np.sqrt(self.TRADING_DAYS)

        # ── Sharpe ────────────────────────────────────────────────────────────
        rf_daily = self.RISK_FREE_RATE / self.TRADING_DAYS
        excess = portfolio_returns - rf_daily
        if metrics.volatility_daily > 0:
            metrics.sharpe_ratio = round(float(np.mean(excess) / metrics.volatility_daily * np.sqrt(self.TRADING_DAYS)), 4)

        # ── Sortino ───────────────────────────────────────────────────────────
        downside = portfolio_returns[portfolio_returns < rf_daily]
        if len(downside) > 0:
            downside_std = float(np.std(downside)) * np.sqrt(self.TRADING_DAYS)
            if downside_std > 0:
                metrics.sortino_ratio = round(float(np.mean(excess)) * self.TRADING_DAYS / downside_std, 4)

        # ── Max Drawdown ──────────────────────────────────────────────────────
        cumulative = (1 + pd.Series(portfolio_returns)).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        metrics.max_drawdown = round(float(drawdown.min()), 4)
        metrics.current_drawdown = round(float(drawdown.iloc[-1]), 4)

        # ── Calmar ────────────────────────────────────────────────────────────
        annual_return = float(np.mean(portfolio_returns)) * self.TRADING_DAYS
        if metrics.max_drawdown and metrics.max_drawdown != 0:
            metrics.calmar_ratio = round(annual_return / abs(metrics.max_drawdown), 4)

        # ── Beta y Alpha vs benchmark ─────────────────────────────────────────
        if benchmark_returns is not None:
            print("=" * 80)
            print("BENCHMARK RECIBIDO")
            print("ROWS:", len(benchmark_returns))
            print("=" * 80)           
            print("AAPL INDEX")
            print(df.index[:5])

            print("SPY INDEX")
            print(benchmark_returns.index[:5])

            bench = benchmark_returns.reindex(df.index).dropna()
            port_aligned = pd.Series(portfolio_returns, index=df.index).reindex(bench.index).dropna()
            print("PORT ALIGNED:", len(port_aligned))
            print("BENCH:", len(bench))
            if len(port_aligned) > 30:
                    cov_matrix = np.cov(port_aligned, bench)
                    benchmark_var = float(np.var(bench))
            
            if benchmark_var > 0:
                    metrics.beta = round(float(cov_matrix[0, 1] / benchmark_var), 4)
                    port_annual = float(np.mean(port_aligned)) * self.TRADING_DAYS
                    bench_annual = float(np.mean(bench)) * self.TRADING_DAYS
                    metrics.alpha = round(port_annual - (self.RISK_FREE_RATE + (metrics.beta or 1) * (bench_annual - self.RISK_FREE_RATE)), 4)
            print("BENCHMARK VAR:", benchmark_var)
            print("BETA:", metrics.beta)
            print("ALPHA:", metrics.alpha)

        # ── Concentración ─────────────────────────────────────────────────────
        sorted_w = sorted(w, reverse=True)
        metrics.top1_concentration = round(float(sorted_w[0]), 4)
        metrics.top5_concentration = round(float(sum(sorted_w[:5])), 4)

        # ── Correlación promedio ──────────────────────────────────────────────
        if len(symbols) > 1:
            corr_matrix = df.corr().values
            upper = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
            metrics.avg_correlation = round(float(np.mean(upper)), 4)
            # Score de diversificación: menor correlación y concentración = mejor
            corr_penalty = (metrics.avg_correlation + 1) / 2   # 0-1
            conc_penalty = metrics.top1_concentration
            metrics.diversification_score = round((1 - (corr_penalty * 0.5 + conc_penalty * 0.5)) * 100, 1)

        # ── Concentración sectorial ───────────────────────────────────────────
        if positions_by_sector:
            metrics.sector_concentration = positions_by_sector

        # ── Label de riesgo global ────────────────────────────────────────────
        metrics.risk_label = self._risk_label(metrics)

        return metrics

    def suggest_rebalancing(
        self,
        weights: dict[str, float],
        metrics: RiskMetrics,
        target_sharpe: float = 1.0,
    ) -> list[dict]:
        """
        Sugiere ajustes de cartera para mejorar diversificación y Sharpe.
        """
        suggestions = []

        if metrics.top1_concentration and metrics.top1_concentration > 0.40:
            symbol = max(weights, key=weights.get)
            suggestions.append({
                "type": "reduce_concentration",
                "symbol": symbol,
                "message": f"{symbol} representa {metrics.top1_concentration*100:.1f}% del portafolio. Considerar reducir a máximo 25-30%.",
                "priority": "high",
            })

        if metrics.avg_correlation and metrics.avg_correlation > 0.75:
            suggestions.append({
                "type": "add_uncorrelated",
                "message": "Correlación promedio alta. Agregar activos poco correlacionados: bonos, commodities, o activos del mercado local.",
                "priority": "medium",
            })

        if metrics.sharpe_ratio and metrics.sharpe_ratio < 0.5:
            suggestions.append({
                "type": "improve_sharpe",
                "message": f"Sharpe Ratio de {metrics.sharpe_ratio:.2f} es bajo. Revisar posiciones con alto riesgo y bajo retorno.",
                "priority": "medium",
            })

        if metrics.volatility_annual and metrics.volatility_annual > 0.35:
            suggestions.append({
                "type": "reduce_volatility",
                "message": f"Volatilidad anualizada del {metrics.volatility_annual*100:.1f}%. Considerar incorporar activos defensivos o aumentar cash.",
                "priority": "high",
            })

        if metrics.max_drawdown and metrics.max_drawdown < -0.25:
            suggestions.append({
                "type": "drawdown_warning",
                "message": f"Drawdown máximo de {metrics.max_drawdown*100:.1f}%. Revisar stops y exposición a activos de alta volatilidad.",
                "priority": "critical",
            })

        return suggestions

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _var(self, returns: np.ndarray, confidence: float) -> float:
        return round(float(np.percentile(returns, (1 - confidence) * 100)), 6)

    def _cvar(self, returns: np.ndarray, confidence: float) -> float:
        var = self._var(returns, confidence)
        tail = returns[returns <= var]
        return round(float(np.mean(tail)), 6) if len(tail) > 0 else var

    def _risk_label(self, m: RiskMetrics) -> str:
        score = 0
        if m.volatility_annual:
            if m.volatility_annual > 0.40: score += 3
            elif m.volatility_annual > 0.25: score += 2
            elif m.volatility_annual > 0.15: score += 1
        if m.max_drawdown:
            if m.max_drawdown < -0.30: score += 3
            elif m.max_drawdown < -0.15: score += 2
            elif m.max_drawdown < -0.08: score += 1
        if m.sharpe_ratio:
            if m.sharpe_ratio < 0: score += 2
            elif m.sharpe_ratio < 0.5: score += 1
        if score >= 6: return "critical"
        if score >= 4: return "high"
        if score >= 2: return "moderate"
        return "low"