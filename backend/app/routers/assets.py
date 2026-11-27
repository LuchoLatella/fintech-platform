from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.asset import Asset
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[AssetResponse],
)
async def get_assets(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset))
    return result.scalars().all()


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset no encontrado",
        )

    return asset


@router.get("/{asset_id}/prices")
async def get_asset_prices(
    asset_id: UUID,
    timeframe: str = Query("1d", pattern="^(1m|5m|15m|1h|4h|1d|1w)$"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Historial de velas OHLCV desde TimescaleDB."""
    result = await db.execute(
        text("""
            SELECT time, open, high, low, close, volume, vwap, source, timeframe
            FROM price_ohlcv
            WHERE asset_id = :asset_id AND timeframe = :timeframe
            ORDER BY time DESC
            LIMIT :limit
        """),
        {"asset_id": str(asset_id), "timeframe": timeframe, "limit": limit},
    )
    rows = result.mappings().all()
    return [dict(r) for r in reversed(rows)]


@router.get("/{asset_id}/latest")
async def get_asset_latest_price(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Última cotización disponible (prioriza price_ticks y hace fallback a price_ohlcv)."""
    tick_res = await db.execute(
        text("""
            SELECT time, price, bid, ask, volume, source, 'tick' AS kind
            FROM price_ticks
            WHERE asset_id = :asset_id
            ORDER BY time DESC
            LIMIT 1
        """),
        {"asset_id": str(asset_id)},
    )
    tick = tick_res.mappings().first()
    if tick:
        return dict(tick)

    ohlcv_res = await db.execute(
        text("""
            SELECT time, close AS price, open, high, low, volume, source, 'ohlcv' AS kind
            FROM price_ohlcv
            WHERE asset_id = :asset_id
            ORDER BY time DESC
            LIMIT 1
        """),
        {"asset_id": str(asset_id)},
    )
    candle = ohlcv_res.mappings().first()
    if not candle:
        raise HTTPException(status_code=404, detail="Sin cotizaciones registradas para este activo")
    return dict(candle)


@router.post(
    "/",
    response_model=AssetResponse,
)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
):
    asset = Asset(**data.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.put(
    "/{asset_id}",
    response_model=AssetResponse,
)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset no encontrado",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset no encontrado",
        )

    await db.delete(asset)
    await db.commit()
    return {"message": "Asset eliminado correctamente"}