"""
Análisis Fundamental — Scoring automático de activos.
Calcula puntajes de valuación, calidad y oportunidad.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import structlog

log = structlog.get_logger()


@dataclass
class FundamentalScore:
    symbol: str
    # Scores normalizados 0-100
    valuation_score: float = 50.0      # subvalorado = alto
    quality_score: float = 50.0        # negocio de calidad = alto
    growth_score: float = 50.0         # crecimiento = alto
    safety_score: float = 50.0         # solidez financiera = alto
    overall_score: float = 50.0        # score compuesto final
    # Clasificación
    label: str = "neutral"             # undervalued | fairly_valued | overvalued
    opportunity: str = "watch"         # buy | watch | avoid
    rationale: str = ""
    # Datos crudos
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_growth: Optional[float] = None
    dividend_yield: Optional[float] = None
    free_cash_flow: Optional[float] = None


class FundamentalAnalyzer:
    """
    Calcula scores fundamentales para un activo dado sus ratios financieros.
    Compara con promedios sectoriales para detectar oportunidades.
    """

    # Benchmarks sectoriales (mediana de mercado)
    SECTOR_BENCHMARKS = {
        "technology":   {"pe": 28, "pb": 5.0, "roe": 0.18, "dte": 0.6},
        "financials":   {"pe": 12, "pb": 1.2, "roe": 0.12, "dte": 1.5},
        "energy":       {"pe": 15, "pb": 1.8, "roe": 0.10, "dte": 0.8},
        "consumer":     {"pe": 20, "pb": 3.0, "roe": 0.15, "dte": 0.7},
        "healthcare":   {"pe": 22, "pb": 3.5, "roe": 0.16, "dte": 0.5},
        "utilities":    {"pe": 18, "pb": 1.5, "roe": 0.09, "dte": 1.2},
        "default":      {"pe": 20, "pb": 2.5, "roe": 0.12, "dte": 0.8},
    }

    def score(self, data: dict, sector: str = "default") -> FundamentalScore:
        """
        Entrada: dict con ratios financieros (de la DB o de la API).
        Salida: FundamentalScore con todos los puntajes y clasificación.
        """
        symbol = data.get("symbol", "UNKNOWN")
        bench = self.SECTOR_BENCHMARKS.get(sector, self.SECTOR_BENCHMARKS["default"])
        result = FundamentalScore(symbol=symbol)

        # Extraer ratios
        pe = data.get("pe_ratio")
        pb = data.get("pb_ratio")
        roe = data.get("roe")
        dte = data.get("debt_to_equity")
        rev_growth = data.get("revenue_growth_yoy")
        div_yield = data.get("dividend_yield")
        fcf = data.get("free_cash_flow")
        current_ratio = data.get("current_ratio")
        eps_growth = data.get("earnings_growth_yoy")

        result.pe_ratio = pe
        result.pb_ratio = pb
        result.roe = roe
        result.debt_to_equity = dte
        result.revenue_growth = rev_growth
        result.dividend_yield = div_yield
        result.free_cash_flow = fcf

        # ── Score de valuación (subvalorado = puntaje alto) ───────────────────
        val_points = []
        reasons_val = []

        if pe is not None and pe > 0:
            ratio = bench["pe"] / pe
            val_points.append(min(100, ratio * 50))
            if pe < bench["pe"] * 0.7:
                reasons_val.append(f"PER bajo ({pe:.1f}x vs benchmark {bench['pe']}x)")
            elif pe > bench["pe"] * 1.5:
                reasons_val.append(f"PER elevado ({pe:.1f}x)")

        if pb is not None and pb > 0:
            ratio = bench["pb"] / pb
            val_points.append(min(100, ratio * 50))
            if pb < bench["pb"] * 0.7:
                reasons_val.append(f"PB bajo ({pb:.1f}x)")

        result.valuation_score = round(sum(val_points) / len(val_points), 1) if val_points else 50.0

        # ── Score de calidad ──────────────────────────────────────────────────
        qual_points = []
        reasons_qual = []

        if roe is not None:
            qual_points.append(min(100, (roe / bench["roe"]) * 50))
            if roe > 0.20:
                reasons_qual.append(f"ROE sólido ({roe*100:.1f}%)")
            elif roe < 0:
                reasons_qual.append("ROE negativo")

        if dte is not None:
            ratio = bench["dte"] / (dte + 0.01)
            qual_points.append(min(100, ratio * 50))
            if dte < bench["dte"] * 0.5:
                reasons_qual.append("baja deuda")
            elif dte > bench["dte"] * 2:
                reasons_qual.append("deuda elevada")

        if fcf is not None and fcf > 0:
            qual_points.append(70)
            reasons_qual.append("flujo de caja positivo")
        elif fcf is not None and fcf < 0:
            qual_points.append(25)

        if div_yield is not None and 0.02 < div_yield < 0.10:
            qual_points.append(65)
            reasons_qual.append(f"dividendo {div_yield*100:.1f}%")

        result.quality_score = round(sum(qual_points) / len(qual_points), 1) if qual_points else 50.0

        # ── Score de crecimiento ──────────────────────────────────────────────
        growth_points = []

        if rev_growth is not None:
            if rev_growth > 0.20:
                growth_points.append(90)
            elif rev_growth > 0.10:
                growth_points.append(70)
            elif rev_growth > 0:
                growth_points.append(55)
            elif rev_growth < -0.10:
                growth_points.append(20)
            else:
                growth_points.append(40)

        if eps_growth is not None:
            if eps_growth > 0.15:
                growth_points.append(85)
            elif eps_growth > 0:
                growth_points.append(60)
            else:
                growth_points.append(30)

        result.growth_score = round(sum(growth_points) / len(growth_points), 1) if growth_points else 50.0

        # ── Score de seguridad ────────────────────────────────────────────────
        safety_points = [50.0]
        if current_ratio is not None:
            if current_ratio > 2:
                safety_points.append(85)
            elif current_ratio > 1:
                safety_points.append(60)
            else:
                safety_points.append(25)
        if dte is not None:
            if dte < 0.3:
                safety_points.append(90)
            elif dte < 1.0:
                safety_points.append(65)
            elif dte > 2.0:
                safety_points.append(25)
            else:
                safety_points.append(45)

        result.safety_score = round(sum(safety_points) / len(safety_points), 1)

        # ── Score compuesto ───────────────────────────────────────────────────
        result.overall_score = round(
            result.valuation_score * 0.35 +
            result.quality_score   * 0.30 +
            result.growth_score    * 0.20 +
            result.safety_score    * 0.15,
            1
        )

        # ── Clasificación final ───────────────────────────────────────────────
        if result.overall_score >= 68 and result.valuation_score >= 60:
            result.label = "undervalued"
            result.opportunity = "buy"
        elif result.overall_score <= 35 or (result.valuation_score <= 25 and result.quality_score <= 40):
            result.label = "overvalued"
            result.opportunity = "avoid"
        elif result.overall_score >= 55:
            result.label = "fairly_valued"
            result.opportunity = "watch"
        else:
            result.label = "fairly_valued"
            result.opportunity = "watch"

        # ── Rationale ─────────────────────────────────────────────────────────
        all_reasons = reasons_val[:2] + reasons_qual[:2]
        if all_reasons:
            result.rationale = (
                f"Activo {result.label.replace('_', ' ')} con score fundamental {result.overall_score:.0f}/100. "
                f"Puntos clave: {', '.join(all_reasons)}."
            )
        else:
            result.rationale = f"Score fundamental {result.overall_score:.0f}/100. Datos limitados disponibles."

        return result

    def compare_peers(self, scores: list[FundamentalScore]) -> list[FundamentalScore]:
        """Ordena activos por score compuesto para comparación sectorial."""
        return sorted(scores, key=lambda x: x.overall_score, reverse=True)


# ── Router ────────────────────────────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db, get_redis
from app.routers.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

analysis_router = APIRouter()


@analysis_router.get("/technical/{symbol}", summary="Análisis técnico completo")
async def get_technical(
    symbol: str,
    timeframe: str = Query("1d"),
    current_user=Depends(get_current_user),
    redis=Depends(get_redis),
):
    from app.services.market_data.provider import MarketDataProvider
    from app.services.analysis.technical import TechnicalAnalysisEngine

    provider = MarketDataProvider(redis_client=redis)
    engine = TechnicalAnalysisEngine()
    try:
        ohlcv = await provider.get_ohlcv(symbol.upper(), timeframe)
        result = engine.analyze(ohlcv.data, symbol.upper(), timeframe)
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "trend": result.trend,
            "strength": result.strength,
            "indicators": {
                "rsi_14": result.rsi_14,
                "macd": {"line": result.macd_line, "signal": result.macd_signal, "hist": result.macd_hist},
                "bollinger": {"upper": result.bb_upper, "middle": result.bb_middle, "lower": result.bb_lower, "width": result.bb_width},
                "emas": {"ema_9": result.ema_9, "ema_21": result.ema_21, "ema_50": result.ema_50, "ema_200": result.ema_200},
                "atr_14": result.atr_14,
                "vwap": result.vwap,
                "stoch": {"k": result.stoch_k, "d": result.stoch_d},
            },
            "signals": result.signals,
            "risk_levels": {
                "stop_loss": result.stop_loss_suggestion,
                "take_profit": result.take_profit_suggestion,
            },
        }
    finally:
        await provider.close()


@analysis_router.get("/fundamental/{symbol}", summary="Análisis fundamental con scoring")
async def get_fundamental(
    symbol: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.asset import Asset
    from sqlalchemy import select, text

    asset_result = await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise HTTPException(404, f"Activo {symbol} no encontrado")

    result = await db.execute(
        text("SELECT * FROM fundamental_data WHERE asset_id = :id ORDER BY period DESC LIMIT 1"),
        {"id": str(asset.id)}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(404, "Sin datos fundamentales para este activo")

    analyzer = FundamentalAnalyzer()
    score = analyzer.score(
        data={**dict(row), "symbol": symbol.upper()},
        sector=asset.sector or "default",
    )

    return {
        "symbol": symbol.upper(),
        "name": asset.name,
        "sector": asset.sector,
        "scores": {
            "overall": score.overall_score,
            "valuation": score.valuation_score,
            "quality": score.quality_score,
            "growth": score.growth_score,
            "safety": score.safety_score,
        },
        "classification": {
            "label": score.label,
            "opportunity": score.opportunity,
            "rationale": score.rationale,
        },
        "ratios": {
            "pe_ratio": score.pe_ratio,
            "pb_ratio": score.pb_ratio,
            "roe": score.roe,
            "debt_to_equity": score.debt_to_equity,
            "revenue_growth": score.revenue_growth,
            "dividend_yield": score.dividend_yield,
        },
        "disclaimer": "Análisis informativo. No constituye asesoramiento financiero.",
    }


@analysis_router.get("/screener", summary="Screener: activos por criterios fundamentales")
async def screener(
    min_roe: Optional[float] = Query(None, description="ROE mínimo (ej: 0.15 = 15%)"),
    max_pe: Optional[float] = Query(None, description="PER máximo"),
    max_debt: Optional[float] = Query(None, description="Deuda/equity máxima"),
    min_growth: Optional[float] = Query(None, description="Crecimiento revenue mínimo"),
    sector: Optional[str] = None,
    limit: int = Query(20, le=50),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Screener fundamental: filtra activos por múltiples criterios.
    Ideal para encontrar candidatos value o growth.
    """
    from sqlalchemy import text

    filters = ["fd.period_type = 'TTM'"]
    params = {}

    if min_roe is not None:
        filters.append("fd.roe >= :min_roe")
        params["min_roe"] = min_roe
    if max_pe is not None:
        filters.append("fd.pe_ratio <= :max_pe AND fd.pe_ratio > 0")
        params["max_pe"] = max_pe
    if max_debt is not None:
        filters.append("fd.debt_to_equity <= :max_debt")
        params["max_debt"] = max_debt
    if min_growth is not None:
        filters.append("fd.revenue_growth_yoy >= :min_growth")
        params["min_growth"] = min_growth
    if sector:
        filters.append("a.sector = :sector")
        params["sector"] = sector

    where_clause = " AND ".join(filters)
    params["limit"] = limit

    result = await db.execute(
        text(f"""
            SELECT a.symbol, a.name, a.sector, fd.pe_ratio, fd.pb_ratio,
                   fd.roe, fd.debt_to_equity, fd.revenue_growth_yoy, fd.dividend_yield,
                   fd.fundamental_score, fd.valuation_score
            FROM fundamental_data fd
            JOIN assets a ON fd.asset_id = a.id
            WHERE {where_clause}
            ORDER BY fd.fundamental_score DESC NULLS LAST, fd.valuation_score DESC NULLS LAST
            LIMIT :limit
        """),
        params
    )
    rows = result.mappings().all()

    analyzer = FundamentalAnalyzer()
    output = []
    for row in rows:
        score = analyzer.score(dict(row), sector=row.get("sector") or "default")
        output.append({
            "symbol": row["symbol"],
            "name": row["name"],
            "sector": row["sector"],
            "overall_score": score.overall_score,
            "opportunity": score.opportunity,
            "pe_ratio": row["pe_ratio"],
            "pb_ratio": row["pb_ratio"],
            "roe": row["roe"],
            "debt_to_equity": row["debt_to_equity"],
            "revenue_growth": row["revenue_growth_yoy"],
            "dividend_yield": row["dividend_yield"],
        })

    return {
        "results": output,
        "count": len(output),
        "filters_applied": {k: v for k, v in params.items() if k != "limit"},
        "disclaimer": "Análisis informativo. No constituye asesoramiento financiero.",
    }