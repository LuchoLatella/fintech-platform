"""
Router: Mercado
Cotizaciones en tiempo real, búsqueda de activos, watchlists y WebSocket.
"""
import asyncio
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.routers.auth import get_current_user

router = APIRouter()


# ── Cotizaciones ──────────────────────────────────────────────────────────────
@router.get("/quote/{symbol}", summary="Cotización en tiempo real")
async def get_quote(
    symbol: str,
    current_user=Depends(get_current_user),
    redis=Depends(get_redis),
):
    from app.services.market_data.provider import MarketDataProvider
    provider = MarketDataProvider(redis_client=redis)
    try:
        quote = await provider.get_quote(symbol.upper())
        return {
            "symbol": quote.symbol,
            "price": quote.price,
            "open": quote.open,
            "high": quote.high,
            "low": quote.low,
            "close": quote.close,
            "volume": quote.volume,
            "change_pct": quote.change_pct,
            "currency": quote.currency,
            "source": quote.source.value,
            "timestamp": str(quote.timestamp),
        }
    except Exception as e:
        raise HTTPException(503, f"No se pudo obtener cotización para {symbol}: {e}")
    finally:
        await provider.close()


@router.get("/history/{symbol}", summary="Datos históricos OHLCV")
async def get_history(
    symbol: str,
    timeframe: str = Query("1d", description="1m|5m|15m|1h|4h|1d|1w"),
    current_user=Depends(get_current_user),
    redis=Depends(get_redis),
):
    from app.services.market_data.provider import MarketDataProvider
    provider = MarketDataProvider(redis_client=redis)
    try:
        ohlcv = await provider.get_ohlcv(symbol.upper(), timeframe)
        df = ohlcv.data.tail(500)   # máximo 500 velas
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "source": ohlcv.source.value,
            "data": [
                {
                    "time": str(row["time"]),
                    "open": round(float(row["open"]), 6),
                    "high": round(float(row["high"]), 6),
                    "low": round(float(row["low"]), 6),
                    "close": round(float(row["close"]), 6),
                    "volume": round(float(row.get("volume", 0)), 2),
                }
                for _, row in df.iterrows()
            ],
            "count": len(df),
        }
    except Exception as e:
        raise HTTPException(503, f"Error al obtener historial: {e}")
    finally:
        await provider.close()


@router.get("/quotes/batch", summary="Cotizaciones múltiples")
async def get_batch_quotes(
    symbols: str = Query(..., description="Símbolos separados por coma: AAPL,MSFT,BTC-USD"),
    current_user=Depends(get_current_user),
    redis=Depends(get_redis),
):
    """Obtiene cotizaciones de múltiples activos en paralelo."""
    from app.services.market_data.provider import MarketDataProvider
    provider = MarketDataProvider(redis_client=redis)
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:20]  # máx 20

    async def fetch_one(sym):
        try:
            q = await provider.get_quote(sym)
            return {"symbol": sym, "price": q.price, "change_pct": q.change_pct,
                    "volume": q.volume, "currency": q.currency, "ok": True}
        except:
            return {"symbol": sym, "ok": False}

    results = await asyncio.gather(*[fetch_one(s) for s in symbol_list])
    await provider.close()
    return {"quotes": results, "count": len(results)}


# ── Búsqueda de activos ───────────────────────────────────────────────────────
@router.get("/search", summary="Buscar activos por nombre o símbolo")
async def search_assets(
    q: str = Query(..., min_length=1),
    asset_class: Optional[str] = None,
    exchange: Optional[str] = None,
    limit: int = Query(20, le=50),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.asset import Asset, AssetClass, Exchange

    query = (
        select(Asset, AssetClass, Exchange)
        .join(AssetClass, Asset.asset_class_id == AssetClass.id)
        .join(Exchange, Asset.exchange_id == Exchange.id)
        .where(
            Asset.is_active == True,
            or_(
                Asset.symbol.ilike(f"{q}%"),
                Asset.name.ilike(f"%{q}%"),
            )
        )
    )
    if asset_class:
        query = query.where(AssetClass.code == asset_class)
    if exchange:
        query = query.where(Exchange.code == exchange)

    query = query.limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return {
        "results": [
            {
                "id": str(a.id),
                "symbol": a.symbol,
                "name": a.name,
                "asset_class": ac.code,
                "exchange": e.code,
                "currency": a.currency,
                "sector": a.sector,
                "is_argentine": a.is_argentine,
            }
            for a, ac, e in rows
        ],
        "count": len(rows),
    }


# ── Watchlists ────────────────────────────────────────────────────────────────
@router.get("/watchlists", summary="Listar watchlists")
async def list_watchlists(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.watchlist import Watchlist, WatchlistItem
    from app.models.asset import Asset

    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.id)
    )
    watchlists = result.scalars().all()
    output = []
    for wl in watchlists:
        items_result = await db.execute(
            select(WatchlistItem, Asset)
            .join(Asset, WatchlistItem.asset_id == Asset.id)
            .where(WatchlistItem.watchlist_id == wl.id)
        )
        items = [
            {"asset_id": str(a.id), "symbol": a.symbol, "name": a.name, "added_at": str(wi.added_at)}
            for wi, a in items_result.all()
        ]
        output.append({
            "id": str(wl.id), "name": wl.name,
            "is_default": wl.is_default, "items": items,
        })
    return output


@router.post("/watchlists/{watchlist_id}/items", status_code=201, summary="Agregar activo a watchlist")
async def add_to_watchlist(
    watchlist_id: str,
    asset_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.watchlist import Watchlist, WatchlistItem

    wl_result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == uuid.UUID(watchlist_id),
            Watchlist.user_id == current_user.id,
        )
    )
    if not wl_result.scalar_one_or_none():
        raise HTTPException(404, "Watchlist no encontrada")

    item = WatchlistItem(watchlist_id=uuid.UUID(watchlist_id), asset_id=uuid.UUID(asset_id))
    db.add(item)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(400, "El activo ya está en la watchlist")
    return {"message": "Activo agregado"}


@router.delete("/watchlists/{watchlist_id}/items/{asset_id}", summary="Quitar activo de watchlist")
async def remove_from_watchlist(
    watchlist_id: str,
    asset_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.watchlist import Watchlist, WatchlistItem

    wl_result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == uuid.UUID(watchlist_id),
            Watchlist.user_id == current_user.id,
        )
    )
    if not wl_result.scalar_one_or_none():
        raise HTTPException(404, "Watchlist no encontrada")

    await db.execute(
        WatchlistItem.__table__.delete().where(
            (WatchlistItem.watchlist_id == uuid.UUID(watchlist_id)) &
            (WatchlistItem.asset_id == uuid.UUID(asset_id))
        )
    )
    await db.commit()
    return {"message": "Activo eliminado de watchlist"}


# ── WebSocket — stream de precios en tiempo real ───────────────────────────────
class ConnectionManager:
    """Gestiona conexiones WebSocket activas."""
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbols: list[str]):
        await websocket.accept()
        for sym in symbols:
            self.active.setdefault(sym, []).append(websocket)

    def disconnect(self, websocket: WebSocket):
        for sym, conns in self.active.items():
            if websocket in conns:
                conns.remove(websocket)

    async def broadcast(self, symbol: str, data: dict):
        conns = self.active.get(symbol, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/quotes")
async def websocket_quotes(websocket: WebSocket, symbols: str = ""):
    """
    WebSocket para streaming de precios en tiempo real.
    Uso: ws://host/ws/v1/quotes?symbols=AAPL,MSFT,BTC-USD

    El cliente recibe actualizaciones cada 10 segundos por símbolo.
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()][:10]
    if not symbol_list:
        await websocket.close(code=1008, reason="No symbols provided")
        return

    await manager.connect(websocket, symbol_list)

    from app.services.market_data.provider import MarketDataProvider

    try:
        while True:
            for symbol in symbol_list:
                provider = MarketDataProvider()
                try:
                    quote = await provider.get_quote(symbol)
                    await websocket.send_json({
                        "type": "quote",
                        "symbol": symbol,
                        "price": quote.price,
                        "change_pct": quote.change_pct,
                        "volume": quote.volume,
                        "timestamp": str(quote.timestamp),
                    })
                except Exception as e:
                    await websocket.send_json({"type": "error", "symbol": symbol, "message": str(e)})
                finally:
                    await provider.close()

            await asyncio.sleep(10)   # actualizar cada 10 segundos

    except WebSocketDisconnect:
        manager.disconnect(websocket)