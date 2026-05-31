from sqlalchemy import select

from app.database import AsyncSessionLocal

from app.models.asset import (
    Exchange,
    AssetClass,
)


EXCHANGES = [
    {
        "code": "NASDAQ",
        "name": "NASDAQ",
        "country": "US",
        "currency": "USD",
        "timezone": "America/New_York",
    },
    {
        "code": "NYSE",
        "name": "New York Stock Exchange",
        "country": "US",
        "currency": "USD",
        "timezone": "America/New_York",
    },
    {
        "code": "BYMA",
        "name": "Bolsa Argentina",
        "country": "AR",
        "currency": "ARS",
        "timezone": "America/Argentina/Buenos_Aires",
    },
    {
        "code": "BINANCE",
        "name": "Binance",
        "country": "GLOBAL",
        "currency": "USD",
        "timezone": "UTC",
    },
]

ASSET_CLASSES = [
    {
        "code": "stock",
        "name": "Stocks",
    },
    {
        "code": "crypto",
        "name": "Cryptocurrency",
    },
    {
        "code": "cedear",
        "name": "CEDEAR",
    },
    {
        "code": "etf",
        "name": "ETF",
    },
    {
        "code": "bond",
        "name": "Bond",
    },
]


class UniverseBootstrap:

    async def bootstrap(self):

        async with AsyncSessionLocal() as db:

            # Exchanges
            for item in EXCHANGES:

                exists = await db.execute(
                    select(Exchange).where(
                        Exchange.code == item["code"]
                    )
                )

                if not exists.scalar_one_or_none():

                    db.add(
                        Exchange(**item)
                    )

            # Asset Classes
            for item in ASSET_CLASSES:

                exists = await db.execute(
                    select(AssetClass).where(
                        AssetClass.code == item["code"]
                    )
                )

                if not exists.scalar_one_or_none():

                    db.add(
                        AssetClass(**item)
                    )

            await db.commit()