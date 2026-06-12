"""
Router: Portafolio
CRUD de portafolios, posiciones, transacciones y métricas de riesgo.
"""
import uuid
from datetime import date, datetime
#from typing import Optional

#
import pandas as pd
import structlog 
from fastapi import APIRouter, Depends, HTTPException, Query
#from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.database import get_db, get_redis
from app.routers.auth import get_current_user
from app.schemas.portfolio import (PortfolioCreate, PortfolioUpdate, PortfolioResponse, TransactionCreate, TransactionResponse, PositionResponse, PortfolioSummary, PortfolioHealth)
from app.models.portfolio import Portfolio

log = structlog.get_logger()
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


# ── Portafolios ───────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=list[PortfolioResponse],
    summary="Listar portafolios del usuario",
)
async def list_portfolios(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.created_at.desc())
    )

    portfolios = result.scalars().all()

    return portfolios


@router.post(
    "/",
    response_model=PortfolioResponse,
)
async def create_portfolio(
    data: PortfolioCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    portfolio = Portfolio(
    user_id=current_user.id,
    name=data.name,
    description=data.description,
    currency=data.currency,
    portfolio_type=data.portfolio_type,
    is_default=data.is_default,
    broker=data.broker,
    broker_account=data.broker_account,
)

    db.add(portfolio)

    await db.commit()
    await db.refresh(portfolio)

    return portfolio


@router.delete("/{portfolio_id}", summary="Eliminar portafolio")
async def delete_portfolio(
    portfolio_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.portfolio import Portfolio
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == uuid.UUID(portfolio_id),
            Portfolio.user_id == current_user.id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Portafolio no encontrado")
    await db.delete(p)
    await db.commit()
    return {"message": "Portafolio eliminado"}


# ── Posiciones ────────────────────────────────────────────────────────────────
@router.get("/{portfolio_id}/positions", summary="Posiciones abiertas con P&L")
async def get_positions(
    portfolio_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Retorna todas las posiciones abiertas con precio actual y P&L no realizado.
    """
    from app.models.portfolio import Portfolio, PortfolioPosition
    from app.models.asset import Asset
    from app.services.market_data.provider import MarketDataProvider

    # Verificar propiedad
    port_result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == uuid.UUID(portfolio_id),
            Portfolio.user_id == current_user.id,
        )
    )
    portfolio = port_result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(404, "Portafolio no encontrado")

    # Obtener posiciones
    pos_result = await db.execute(
        select(PortfolioPosition, Asset)
        .join(Asset, PortfolioPosition.asset_id == Asset.id)
        .where(PortfolioPosition.portfolio_id == uuid.UUID(portfolio_id), PortfolioPosition.is_open == True)
    )
    rows = pos_result.all()

    if not rows:
        return {"positions": [], "total_value": 0, "total_cost": 0, "total_pnl": 0}

    provider = MarketDataProvider(redis_client=redis)
    positions_out = []
    total_value = 0.0
    total_cost = 0.0

    for position, asset in rows:
        cost_basis = float(position.quantity) * float(position.avg_cost)
        total_cost += cost_basis

        # Obtener precio actual
        current_price = None
        market_value = None
        pnl = None
        pnl_pct = None

        try:

            quote = await provider.get_quote(
                asset.symbol
            )

            current_price = quote.price

            market_value = (
                float(position.quantity)
                * current_price
            )

            pnl = market_value - cost_basis

            pnl_pct = (
                pnl / cost_basis * 100
                if cost_basis > 0
                else 0
            )

            total_value += market_value

        except Exception as e:

            log.error(
                "position_quote_failed",
                symbol=asset.symbol,
                error=str(e)
            )

            current_price = None
            market_value = None
            pnl = None
            pnl_pct = None
        
        positions_out.append({
            "asset_id": str(asset.id),
            "symbol": asset.symbol,
            "name": asset.name,
            "quantity": float(position.quantity),
            "avg_cost": float(position.avg_cost),
            "current_price": round(current_price, 4) if current_price else None,
            "market_value": round(market_value, 2) if market_value else None,
            "cost_basis": round(cost_basis, 2),
            "unrealized_pnl": round(pnl, 2) if pnl is not None else None,
            "unrealized_pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            "weight": None,  # se calcula abajo
        })

    # Calcular pesos
    for p in positions_out:
        if total_value > 0 and p["market_value"]:
            p["weight"] = round(p["market_value"] / total_value * 100, 2)

    await provider.close()

    return {
        "positions": positions_out,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_pnl": round(total_value - total_cost, 2),
        "total_pnl_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
        "currency": portfolio.currency,
    }

# endpoints adicionales para snapshots, resumen, rebalanceo, etc. se pueden agregar aquí siguiendo la misma estructura.

@router.get(
    "/{portfolio_id}/summary",
    response_model=PortfolioSummary,
    summary="Resumen ejecutivo del portafolio",
)
async def get_portfolio_summary(
    portfolio_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.portfolio import Portfolio
    from app.models.portfolio import PortfolioPosition

    portfolio = (
        await db.execute(
            select(Portfolio).where(
                Portfolio.id == uuid.UUID(portfolio_id),
                Portfolio.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()

    if not portfolio:
        raise HTTPException(404, "Portafolio no encontrado")

    positions = (
        await db.execute(
            select(PortfolioPosition).where(
                PortfolioPosition.portfolio_id == portfolio.id,
                PortfolioPosition.is_open == True,
            )
        )
    ).scalars().all()

    return PortfolioSummary(
        portfolio_id=portfolio.id,
        total_positions=len(positions),
        total_value_usd=Decimal("0"),
        cash_balance=portfolio.cash_balance or Decimal("0"),
        total_return=None,
        risk_score=None,
        recommendation_count=0,
    )

@router.get(
    "/{portfolio_id}/health",
    response_model=PortfolioHealth,
    summary="Estado general del portafolio",
)
async def get_portfolio_health(
    portfolio_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    from app.models.asset import Asset
    from app.models.portfolio import PortfolioPosition
    from app.services.analysis.risk import RiskService
    from app.services.copilot.portfolio_health import (
        PortfolioHealthService,
    )
    from app.services.market_data.provider import (
        MarketDataProvider,
    )

    portfolio = (
        await db.execute(
            select(Portfolio).where(
                Portfolio.id == uuid.UUID(portfolio_id),
                Portfolio.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()

    if not portfolio:
        raise HTTPException(
            404,
            "Portafolio no encontrado",
        )

    rows = (
        await db.execute(
            select(
                PortfolioPosition,
                Asset,
            )
            .join(
                Asset,
                PortfolioPosition.asset_id == Asset.id,
            )
            .where(
                PortfolioPosition.portfolio_id
                == portfolio.id,
                PortfolioPosition.is_open == True,
            )
        )
    ).all()

    if not rows:
        return PortfolioHealth(
            score=0,
            status="empty",
            strengths=[],
            warnings=["Portafolio sin posiciones"],
        )

    provider = MarketDataProvider(
        redis_client=redis,
    )

    all_returns = {}
    weights = {}
    total_value = 0

    for position, asset in rows:

        try:

            ohlcv = await provider.get_ohlcv(
                asset.symbol,
                "1d",
            )

            returns = (
                ohlcv.data
                .set_index("time")["close"]
                .pct_change()
                .dropna()
            )

            all_returns[
                asset.symbol
            ] = returns

            quote = await provider.get_quote(
                asset.symbol
            )

            mv = (
                float(position.quantity)
                * quote.price
            )

            weights[asset.symbol] = mv

            total_value += mv

        except Exception as e:

            log.warning(
                "health_data_failed",
                symbol=asset.symbol,
                error=str(e),
            )

    await provider.close()

    if not all_returns:
        raise HTTPException(
            503,
            "No se pudieron obtener datos",
        )

    weights = {
        k: v / total_value
        for k, v in weights.items()
    }

    returns_df = pd.DataFrame(
        all_returns
    ).dropna()

    risk_service = RiskService()

    risk_metrics = (
        risk_service.calculate_portfolio_risk(
            returns_df,
            weights,
        )
    )

    health_service = PortfolioHealthService()

    health = health_service.calculate(
        risk_metrics=risk_metrics,
        total_positions=len(rows),
    )

    return PortfolioHealth(**health)

# ── Transacciones ─────────────────────────────────────────────────────────────
@router.post("/{portfolio_id}/transactions", status_code=201, summary="Registrar compra/venta")
async def add_transaction(
    portfolio_id: str,
    data: TransactionCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra una transacción y actualiza la posición correspondiente.
    Recalcula el precio promedio ponderado en compras.
    """
    from app.models.portfolio import Portfolio, PortfolioPosition, PortfolioTransaction

    port_result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == uuid.UUID(portfolio_id),
            Portfolio.user_id == current_user.id,
        )
    )
    if not port_result.scalar_one_or_none():
        raise HTTPException(404, "Portafolio no encontrado")

    asset_id = uuid.UUID(data.asset_id)

    # Registrar transacción
    tx = PortfolioTransaction(
        portfolio_id=uuid.UUID(portfolio_id),
        asset_id=asset_id,
        transaction_type=data.transaction_type,
        quantity=data.quantity,
        price=data.price,
        commission=data.commission,
        currency=data.currency,
        fx_rate=data.fx_rate,
        notes=data.notes,
        executed_at=data.executed_at,
    )
    db.add(tx)

    # Actualizar posición
    pos_result = await db.execute(
        select(PortfolioPosition).where(
            PortfolioPosition.portfolio_id == uuid.UUID(portfolio_id),
            PortfolioPosition.asset_id == asset_id,
            PortfolioPosition.is_open == True,
        )
    )
    position = pos_result.scalar_one_or_none()

    if data.transaction_type == "buy":
        if position:

            old_value = float(position.quantity) * float(position.avg_cost)

            new_value = float(data.quantity) * float(data.price)

            new_qty = float(position.quantity) + float(data.quantity)

            position.avg_cost = (
                (old_value + new_value) / new_qty
                if new_qty > 0
                else float(data.price)
            )

            position.quantity = new_qty

        else:
            position = PortfolioPosition(
                portfolio_id=uuid.UUID(portfolio_id),
                asset_id=asset_id,
                quantity=float(data.quantity),
                avg_cost=float(data.price),
                currency=data.currency,
            )

            db.add(position)

    elif data.transaction_type == "sell" and position:
        new_qty = float(position.quantity) - float(data.quantity)
        if new_qty <= 0:
            position.quantity = 0
            position.is_open = False
            position.closed_at = datetime.utcnow()
        else:
            position.quantity = new_qty

    await db.flush()
    await db.refresh(tx)
    await db.commit()
    return {"message": "Transacción registrada", "transaction_id": str(tx.id)}


@router.get("/{portfolio_id}/transactions", summary="Historial de transacciones")
async def get_transactions(
    portfolio_id: str,
    limit: int = Query(50, le=200),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.portfolio import Portfolio, PortfolioTransaction
    from app.models.asset import Asset

    port_result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == uuid.UUID(portfolio_id),
            Portfolio.user_id == current_user.id,
        )
    )
    if not port_result.scalar_one_or_none():
        raise HTTPException(404, "Portafolio no encontrado")

    result = await db.execute(
        select(PortfolioTransaction, Asset)
        .join(Asset, PortfolioTransaction.asset_id == Asset.id)
        .where(PortfolioTransaction.portfolio_id == uuid.UUID(portfolio_id))
        .order_by(PortfolioTransaction.executed_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": str(tx.id),
            "symbol": asset.symbol,
            "name": asset.name,
            "type": tx.transaction_type,
            "quantity": float(tx.quantity),
            "price": float(tx.price),
            "commission": float(tx.commission),
            "total": round(float(tx.quantity) * float(tx.price) + float(tx.commission), 2),
            "currency": tx.currency,
            "executed_at": str(tx.executed_at),
            "notes": tx.notes,
        }
        for tx, asset in rows
    ]


# ── Métricas de riesgo ────────────────────────────────────────────────────────
@router.get("/{portfolio_id}/risk", summary="Métricas de riesgo del portafolio")
async def get_risk_metrics(
    portfolio_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Calcula VaR, Sharpe, Beta, Max Drawdown, diversificación y sugerencias de rebalanceo.
    """
    from app.models.portfolio import Portfolio, PortfolioPosition
    from app.models.asset import Asset
    from app.services.market_data.provider import MarketDataProvider
    from app.services.analysis.risk import RiskService

    cache_key = f"risk:{portfolio_id}"
    
    try:
        if redis:
            cached = await redis.get(cache_key)

            if cached:
                import json
                return json.loads(cached)
            
    except Exception as e:
        log.warning("redis_cache_failed", error=str(e))

    port_result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == uuid.UUID(portfolio_id),
            Portfolio.user_id == current_user.id,
        )
    )
    if not port_result.scalar_one_or_none():
        raise HTTPException(404, "Portafolio no encontrado")

    pos_result = await db.execute(
        select(PortfolioPosition, Asset)
        .join(Asset, PortfolioPosition.asset_id == Asset.id)
        .where(PortfolioPosition.portfolio_id == uuid.UUID(portfolio_id), PortfolioPosition.is_open == True)
    )
    rows = pos_result.all()
    if not rows:
        return {"error": "Sin posiciones para calcular riesgo"}

    provider = MarketDataProvider(redis_client=redis)
    risk_svc = RiskService()

    # Obtener retornos históricos de cada posición
    all_returns = {}
    weights = {}
    total_value = 0.0

    for position, asset in rows:
        try:
            ohlcv = await provider.get_ohlcv(asset.symbol, "1d")
            closes = ohlcv.data.set_index("time")["close"]
            returns = closes.pct_change().dropna()
            all_returns[asset.symbol] = returns

            quote = await provider.get_quote(asset.symbol)
            mv = float(position.quantity) * quote.price
            weights[asset.symbol] = mv
            total_value += mv
        except Exception as e:
            log.warning("risk_data_failed", symbol=asset.symbol, error=str(e))

    await provider.close()

    if not all_returns:
        raise HTTPException(503, "No se pudieron obtener datos históricos")

    # Normalizar pesos
    if total_value > 0:
        weights = {k: v / total_value for k, v in weights.items()}

    returns_df = pd.DataFrame(all_returns).dropna()
    metrics = risk_svc.calculate_portfolio_risk(returns_df, weights)
    suggestions = risk_svc.suggest_rebalancing(weights, metrics)

    result = {
        "portfolio_id": portfolio_id,
        "risk_label": metrics.risk_label,
        "var": {
            "var_95_1d": metrics.var_95_1d,
            "var_99_1d": metrics.var_99_1d,
            "cvar_95_1d": metrics.cvar_95_1d,
            "interpretation": f"Con 95% de confianza, la pérdida máxima diaria no supera {abs(metrics.var_95_1d or 0)*100:.2f}% del portafolio.",
        },
        "performance": {
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "calmar_ratio": metrics.calmar_ratio,
            "volatility_daily": metrics.volatility_daily,
            "volatility_annual": metrics.volatility_annual,
        },
        "drawdown": {
            "max_drawdown": metrics.max_drawdown,
            "current_drawdown": metrics.current_drawdown,
        },
        "market": {
            "beta": metrics.beta,
            "alpha": metrics.alpha,
        },
        "diversification": {
            "score": metrics.diversification_score,
            "top1_concentration": metrics.top1_concentration,
            "top5_concentration": metrics.top5_concentration,
            "avg_correlation": metrics.avg_correlation,
            "sector_concentration": metrics.sector_concentration,
        },
        "suggestions": suggestions,
        "disclaimer": "Métricas calculadas con datos históricos. No garantizan resultados futuros.",
        "calculated_at": str(datetime.utcnow()),
    }

    try:
        if redis:
            import json
            await redis.setex(cache_key, 300, json.dumps(result, default=str))

    except Exception as e:        
        log.warning("redis_cache_failed", error=str(e))

    return result

@router.get("/test-aapl")
async def test_aapl():

    from app.services.market_data.provider import (
        MarketDataProvider
    )

    provider = MarketDataProvider()

    quote = await provider.get_quote("AAPL")

    await provider.close()

    return {
        "symbol": quote.symbol,
        "price": quote.price,
        "source": quote.source
    }

@router.get("/test-settings")
async def test_settings():
    from app.config import settings

    return {
        "DATABASE_URL": settings.DATABASE_URL,
        "REDIS_URL": settings.REDIS_URL,
        "ALPHA_VANTAGE_KEY": bool(settings.ALPHA_VANTAGE_KEY),
        "FINNHUB_KEY": bool(settings.FINNHUB_KEY),
    }


