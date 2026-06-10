from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.crud.portfolio_transaction import (
    create_transaction,
    get_transactions,
    get_transaction,
    update_transaction,
    delete_transaction
)

from app.schemas.portfolio_transaction import (
    PortfolioTransactionCreate,
    PortfolioTransactionUpdate,
    PortfolioTransactionResponse
)

router = APIRouter(
    tags=["Portfolio Transactions"]
)


# ==========================================================
# CREATE
# ==========================================================

@router.post(
    "/portfolios/{portfolio_id}/transactions",
    response_model=PortfolioTransactionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_transaction_endpoint(
    portfolio_id: UUID,
    transaction_in: PortfolioTransactionCreate,
    db: AsyncSession = Depends(get_db)
):

    return await create_transaction(
        db=db,
        portfolio_id=portfolio_id,
        transaction_in=transaction_in
    )


# ==========================================================
# LIST
# ==========================================================

@router.get(
    "/portfolios/{portfolio_id}/transactions",
    response_model=list[PortfolioTransactionResponse]
)
async def list_transactions(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    return await get_transactions(
        db=db,
        portfolio_id=portfolio_id
    )


# ==========================================================
# GET BY ID
# ==========================================================

@router.get(
    "/transactions/{transaction_id}",
    response_model=PortfolioTransactionResponse
)
async def get_transaction_endpoint(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    transaction = await get_transaction(
        db=db,
        transaction_id=transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


# ==========================================================
# UPDATE
# ==========================================================

@router.put(
    "/transactions/{transaction_id}",
    response_model=PortfolioTransactionResponse
)
async def update_transaction_endpoint(
    transaction_id: UUID,
    transaction_in: PortfolioTransactionUpdate,
    db: AsyncSession = Depends(get_db)
):

    transaction = await get_transaction(
        db=db,
        transaction_id=transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return await update_transaction(
        db=db,
        transaction=transaction,
        transaction_in=transaction_in
    )


# ==========================================================
# DELETE
# ==========================================================

@router.delete(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_transaction_endpoint(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    transaction = await get_transaction(
        db=db,
        transaction_id=transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    await delete_transaction(
        db=db,
        transaction=transaction
    )

    return None