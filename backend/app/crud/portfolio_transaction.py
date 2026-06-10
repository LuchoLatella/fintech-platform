from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import (
    PortfolioTransaction
)

from app.schemas.portfolio_transaction import (
    PortfolioTransactionCreate,
    PortfolioTransactionUpdate
)

########################################################################################

async def create_transaction(
    db: AsyncSession,
    portfolio_id: UUID,
    transaction_in: PortfolioTransactionCreate
):

    transaction = PortfolioTransaction(
        portfolio_id=portfolio_id,
        **transaction_in.model_dump()
    )

    db.add(transaction)

    await db.commit()

    await db.refresh(transaction)

    return transaction

async def get_transactions(
    db: AsyncSession,
    portfolio_id: UUID
):

    result = await db.execute(
        select(PortfolioTransaction)
        .where(
            PortfolioTransaction.portfolio_id
            == portfolio_id
        )
    )

    return result.scalars().all()

async def get_transaction(
    db: AsyncSession,
    transaction_id: UUID
):

    result = await db.execute(
        select(PortfolioTransaction)
        .where(
            PortfolioTransaction.id
            == transaction_id
        )
    )

    return result.scalar_one_or_none()

async def update_transaction(
    db: AsyncSession,
    transaction: PortfolioTransaction,
    transaction_in: PortfolioTransactionUpdate
):

    update_data = transaction_in.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()

    await db.refresh(transaction)

    return transaction

async def delete_transaction(
    db: AsyncSession,
    transaction: PortfolioTransaction
):

    await db.delete(transaction)

    await db.commit()

    