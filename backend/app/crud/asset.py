from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


async def create_asset(
    db: AsyncSession,
    asset_in: AssetCreate
):

    asset = Asset(**asset_in.model_dump())

    db.add(asset)

    await db.commit()
    await db.refresh(asset)

    return asset


async def get_assets(
    db: AsyncSession
):

    result = await db.execute(
        select(Asset)
    )

    return result.scalars().all()


async def get_asset(
    db: AsyncSession,
    asset_id: UUID
):

    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id
        )
    )

    return result.scalar_one_or_none()


async def update_asset(
    db: AsyncSession,
    asset: Asset,
    asset_in: AssetUpdate
):

    update_data = asset_in.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)

    return asset


async def delete_asset(
    db: AsyncSession,
    asset: Asset
):

    await db.delete(asset)
    await db.commit()