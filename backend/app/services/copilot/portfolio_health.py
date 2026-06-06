from app.services.analysis.risk import RiskMetrics


class PortfolioHealthService:

    def calculate(
        self,
        risk_metrics: RiskMetrics,
        total_positions: int,
    ) -> dict:

        score = 100

        strengths = []
        warnings = []

        # Diversificación
        if total_positions >= 10:
            strengths.append("Buena diversificación por cantidad de posiciones")
        elif total_positions < 3:
            score -= 15
            warnings.append("Muy pocas posiciones abiertas")

        # Concentración
        if (
            risk_metrics.top1_concentration
            and risk_metrics.top1_concentration > 0.40
        ):
            score -= 20
            warnings.append(
                "Alta concentración en una única posición"
            )

        # Sharpe
        if risk_metrics.sharpe_ratio:

            if risk_metrics.sharpe_ratio > 1:
                strengths.append(
                    "Excelente rendimiento ajustado por riesgo"
                )

            elif risk_metrics.sharpe_ratio < 0.5:
                score -= 10
                warnings.append(
                    "Sharpe Ratio bajo"
                )

        # Drawdown
        if (
            risk_metrics.max_drawdown
            and risk_metrics.max_drawdown < -0.20
        ):
            score -= 15
            warnings.append(
                "Drawdown elevado"
            )

        # Volatilidad
        if (
            risk_metrics.volatility_annual
            and risk_metrics.volatility_annual > 0.35
        ):
            score -= 10
            warnings.append(
                "Volatilidad superior a la recomendada"
            )

        score = max(0, min(100, score))

        if score >= 80:
            status = "excellent"
        elif score >= 65:
            status = "good"
        elif score >= 50:
            status = "moderate"
        else:
            status = "poor"

        return {
            "score": score,
            "status": status,
            "strengths": strengths,
            "warnings": warnings,
        }