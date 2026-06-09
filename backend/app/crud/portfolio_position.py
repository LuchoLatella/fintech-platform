from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import PortfolioPosition
from app.schemas.portfolio_position import (
    PortfolioPositionCreate,
    PortfolioPositionUpdate
)

#################################################################################

async def create_position(
    db: AsyncSession,
    portfolio_id: UUID,
    position_in: PortfolioPositionCreate
):
    position = PortfolioPosition(
        portfolio_id=portfolio_id,
        **position_in.model_dump()
    )

    db.add(position)

    await db.commit()
    await db.refresh(position)

    return position

async def get_positions(
    db: AsyncSession,
    portfolio_id: UUID
):
    result = await db.execute(
        select(PortfolioPosition)
        .where(
            PortfolioPosition.portfolio_id == portfolio_id
        )
    )

    return result.scalars().all()

async def get_position(
    db: AsyncSession,
    position_id: UUID
):
    result = await db.execute(
        select(PortfolioPosition)
        .where(
            PortfolioPosition.id == position_id
        )
    )

    return result.scalar_one_or_none()

async def update_position(
    db: AsyncSession,
    position: PortfolioPosition,
    position_in: PortfolioPositionUpdate
):
    data = position_in.model_dump(
        exclude_unset=True
    )

    for field, value in data.items():
        setattr(position, field, value)

    await db.commit()
    await db.refresh(position)

    return position

async def delete_position(
    db: AsyncSession,
    position: PortfolioPosition
):
    await db.delete(position)
    await db.commit()

    