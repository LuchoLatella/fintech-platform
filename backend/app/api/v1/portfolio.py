from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.crud.portfolio import (
    create_portfolio,
    get_portfolios,
    get_portfolio,
    update_portfolio,
    delete_portfolio
)

from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse
)

router = APIRouter(
    prefix="/portfolios",
    tags=["Portfolios"]
)

# ==========================================================
# TEMPORAL
# luego vendrá desde JWT
# ==========================================================

TEST_USER_ID = UUID("aff9e3f0-8267-402d-acb5-c91479209254")


# ==========================================================
# CREATE
# ==========================================================

@router.post(
    "/",
    response_model=PortfolioResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_portfolio_endpoint(
    portfolio_in: PortfolioCreate,
    db: AsyncSession = Depends(get_db)
):
    portfolio = await create_portfolio(
        db=db,
        user_id=TEST_USER_ID,
        portfolio_in=portfolio_in
    )

    return portfolio


# ==========================================================
# LIST
# ==========================================================

@router.get(
    "/",
    response_model=list[PortfolioResponse]
)
async def list_portfolios(
    db: AsyncSession = Depends(get_db)
):
    return await get_portfolios(
        db=db,
        user_id=TEST_USER_ID
    )


# ==========================================================
# GET BY ID
# ==========================================================

@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse
)
async def get_portfolio_endpoint(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio(
        db=db,
        portfolio_id=portfolio_id
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found"
        )

    return portfolio


# ==========================================================
# UPDATE
# ==========================================================

@router.put(
    "/{portfolio_id}",
    response_model=PortfolioResponse
)
async def update_portfolio_endpoint(
    portfolio_id: UUID,
    portfolio_in: PortfolioUpdate,
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio(
        db=db,
        portfolio_id=portfolio_id
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found"
        )

    return await update_portfolio(
        db=db,
        portfolio=portfolio,
        portfolio_in=portfolio_in
    )


# ==========================================================
# DELETE
# ==========================================================

@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_portfolio_endpoint(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio(
        db=db,
        portfolio_id=portfolio_id
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found"
        )

    await delete_portfolio(
        db=db,
        portfolio=portfolio
    )

    return None