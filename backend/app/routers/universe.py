from fastapi import APIRouter

from app.services.universe.bootstrap import (
    UniverseBootstrap,
)

from app.services.universe.loader import (
    UniverseLoader,
)

router = APIRouter()

bootstrap = UniverseBootstrap()

loader = UniverseLoader()


@router.post("/bootstrap")
async def bootstrap_universe():

    await bootstrap.bootstrap()

    return {
        "status": "universe bootstrapped"
    }


@router.post("/sync/nasdaq")
async def sync_nasdaq():

    await loader.load_nasdaq()

    return {
        "status": "NASDAQ synced"
    }