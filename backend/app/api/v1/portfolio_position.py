from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.crud.portfolio_position import (
    create_position,
    get_positions,
    get_position,
    update_position,
    delete_position
)

from app.schemas.portfolio_position import (
    PortfolioPositionCreate,
    PortfolioPositionUpdate,
    PortfolioPositionResponse
)

router = APIRouter(
    prefix="/portfolio-positions",
    tags=["Portfolio Positions"]
)

##############################################################################################################

@router.post(
    "/",
    response_model=PortfolioPositionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_position_endpoint(
    portfolio_id: UUID,
    position_in: PortfolioPositionCreate,
    db: AsyncSession = Depends(get_db)
):
    return await create_position(
        db=db,
        portfolio_id=portfolio_id,
        position_in=position_in
    )

@router.get(
    "/",
    response_model=list[PortfolioPositionResponse]
)
async def list_positions(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    return await get_positions(
        db=db,
        portfolio_id=portfolio_id
    )

@router.get(
    "/{position_id}",
    response_model=PortfolioPositionResponse
)
async def get_position_endpoint(
    position_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    position = await get_position(
        db=db,
        position_id=position_id
    )

    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found"
        )

    return position

@router.put(
    "/{position_id}",
    response_model=PortfolioPositionResponse
)
async def update_position_endpoint(
    position_id: UUID,
    position_in: PortfolioPositionUpdate,
    db: AsyncSession = Depends(get_db)
):
    position = await get_position(
        db=db,
        position_id=position_id
    )

    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found"
        )

    return await update_position(
        db=db,
        position=position,
        position_in=position_in
    )

@router.delete(
    "/{position_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_position_endpoint(
    position_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    position = await get_position(
        db=db,
        position_id=position_id
    )

    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found"
        )

    await delete_position(
        db=db,
        position=position
    )

    return None

