from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import PortfolioPosition


async def update_position_after_transaction(
    db: AsyncSession,
    portfolio_id,
    transaction
):
    """
    Actualiza automáticamente una posición
    cuando se registra una transacción BUY o SELL.
    """

    result = await db.execute(
        select(PortfolioPosition).where(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.asset_id == transaction.asset_id,
            PortfolioPosition.is_open == True
        )
    )

    position = result.scalar_one_or_none()

    # ==================================================
    # BUY
    # ==================================================

    if transaction.transaction_type.upper() == "BUY":

        if not position:

            position = PortfolioPosition(
                portfolio_id=portfolio_id,
                asset_id=transaction.asset_id,
                quantity=transaction.quantity,
                avg_cost=transaction.price,
                currency=transaction.currency,
                is_open=True,
            )

            db.add(position)

            return position

        old_quantity = Decimal(position.quantity)
        old_cost = Decimal(position.avg_cost)

        new_quantity = Decimal(transaction.quantity)
        new_price = Decimal(transaction.price)

        total_quantity = old_quantity + new_quantity

        weighted_cost = (
            (old_quantity * old_cost)
            + (new_quantity * new_price)
        ) / total_quantity

        position.quantity = total_quantity
        position.avg_cost = weighted_cost

        return position

    # ==================================================
    # SELL
    # ==================================================

    if transaction.transaction_type.upper() == "SELL":

        if not position:

            raise ValueError(
                "No existe posición abierta para vender"
            )

        remaining_quantity = (
            Decimal(position.quantity)
            - Decimal(transaction.quantity)
        )

        if remaining_quantity < 0:

            raise ValueError(
                "No hay suficientes activos para vender"
            )

        position.quantity = remaining_quantity

        if remaining_quantity == 0:

            position.is_open = False
            position.closed_at = datetime.utcnow()

        return position