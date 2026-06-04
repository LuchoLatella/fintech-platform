from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.asset import Asset
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[AssetResponse],
)
async def get_assets(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Asset)
    )

    return result.scalars().all()


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id
        )
    )

    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset no encontrado",
        )

    return asset


@router.post(
    "/",
    response_model=AssetResponse,
)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
):
    asset = Asset(
        **data.model_dump()
    )

    db.add(asset)

    await db.commit()

    await db.refresh(asset)

    return asset