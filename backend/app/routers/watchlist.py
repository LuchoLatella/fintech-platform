from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.models.watchlist import (
    Watchlist,
    WatchlistItem,
)

from app.models.user import User

from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistItemCreate,
    WatchlistItemResponse,
)

router = APIRouter()


# ============================================================
# WATCHLISTS
# ============================================================

@router.get(
    "/",
    response_model=list[WatchlistResponse]
)
async def get_watchlists(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Watchlist)
    )

    return result.scalars().all()


@router.get(
    "/{watchlist_id}",
    response_model=WatchlistResponse
)
async def get_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id)
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=404,
            detail="Watchlist no encontrada"
        )

    return watchlist


@router.post(
    "/",
    response_model=WatchlistResponse
)
async def create_watchlist(
    data: WatchlistCreate,
    db: AsyncSession = Depends(get_db)
):
    # Obtener cualquier usuario existente
    user_result = await db.execute(
        select(User).limit(1)
    )

    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="No existe ningún usuario para asociar la watchlist"
        )

    watchlist = Watchlist(
        user_id=user.id,
        name=data.name,
        description=data.description,
    )

    db.add(watchlist)

    await db.commit()
    await db.refresh(watchlist)

    return watchlist


@router.put(
    "/{watchlist_id}",
    response_model=WatchlistResponse
)
async def update_watchlist(
    watchlist_id: UUID,
    data: WatchlistUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id)
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=404,
            detail="Watchlist no encontrada"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(watchlist, field, value)

    await db.commit()
    await db.refresh(watchlist)

    return watchlist


@router.delete(
    "/{watchlist_id}"
)
async def delete_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id)
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=404,
            detail="Watchlist no encontrada"
        )

    await db.delete(watchlist)
    await db.commit()

    return {
        "message": "Watchlist eliminada correctamente"
    }


# ============================================================
# ITEMS
# ============================================================

@router.get(
    "/{watchlist_id}/items",
    response_model=list[WatchlistItemResponse]
)
async def get_watchlist_items(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.watchlist_id == watchlist_id
        )
    )

    return result.scalars().all()


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse
)
async def add_asset_to_watchlist(
    watchlist_id: UUID,
    data: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id)
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=404,
            detail="Watchlist no encontrada"
        )

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        asset_id=data.asset_id,
        notes=data.notes,
    )

    db.add(item)

    await db.commit()
    await db.refresh(item)

    return item


@router.delete(
    "/{watchlist_id}/items/{asset_id}"
)
async def remove_asset_from_watchlist(
    watchlist_id: UUID,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.asset_id == asset_id,
        )
    )

    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Activo no encontrado en la watchlist"
        )

    await db.delete(item)
    await db.commit()

    return {
        "message": "Activo eliminado de la watchlist"
    }