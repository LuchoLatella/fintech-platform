from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


# ==========================================================
# CREATE
# ==========================================================

async def create_portfolio(
    db: AsyncSession,
    user_id: UUID,
    portfolio_in: PortfolioCreate
) -> Portfolio:

    portfolio = Portfolio(
        user_id=user_id,
        name=portfolio_in.name,
        description=portfolio_in.description,
        currency=portfolio_in.currency,
        portfolio_type=portfolio_in.portfolio_type,
        is_default=portfolio_in.is_default,
        broker=portfolio_in.broker,
        broker_account=portfolio_in.broker_account
    )

    db.add(portfolio)

    await db.commit()
    await db.refresh(portfolio)

    return portfolio


# ==========================================================
# LIST
# ==========================================================

async def get_portfolios(
    db: AsyncSession,
    user_id: UUID
):

    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user_id)
    )

    return result.scalars().all()


# ==========================================================
# GET BY ID
# ==========================================================

async def get_portfolio(
    db: AsyncSession,
    portfolio_id: UUID
):

    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id)
    )

    return result.scalar_one_or_none()


# ==========================================================
# UPDATE
# ==========================================================

async def update_portfolio(
    db: AsyncSession,
    portfolio: Portfolio,
    portfolio_in: PortfolioUpdate
):

    update_data = portfolio_in.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(portfolio, field, value)

    await db.commit()
    await db.refresh(portfolio)

    return portfolio


# ==========================================================
# DELETE
# ==========================================================

async def delete_portfolio(
    db: AsyncSession,
    portfolio: Portfolio
):

    await db.delete(portfolio)

    await db.commit()

    return True