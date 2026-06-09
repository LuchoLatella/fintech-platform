from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.crud.asset import (
    create_asset,
    get_assets,
    get_asset,
    update_asset,
    delete_asset
)

from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse
)

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


# CREATE

@router.post(
    "/",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_asset_endpoint(
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db)
):

    return await create_asset(
        db=db,
        asset_in=asset_in
    )


# LIST

@router.get(
    "/",
    response_model=list[AssetResponse]
)
async def list_assets(
    db: AsyncSession = Depends(get_db)
):

    return await get_assets(db)


# GET BY ID

@router.get(
    "/{asset_id}",
    response_model=AssetResponse
)
async def get_asset_endpoint(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    asset = await get_asset(
        db,
        asset_id
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset


# UPDATE

@router.put(
    "/{asset_id}",
    response_model=AssetResponse
)
async def update_asset_endpoint(
    asset_id: UUID,
    asset_in: AssetUpdate,
    db: AsyncSession = Depends(get_db)
):

    asset = await get_asset(
        db,
        asset_id
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return await update_asset(
        db=db,
        asset=asset,
        asset_in=asset_in
    )


# DELETE

@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_asset_endpoint(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    asset = await get_asset(
        db,
        asset_id
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    await delete_asset(
        db,
        asset
    )

    return None