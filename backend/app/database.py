"""
Gestión de conexiones a PostgreSQL (SQLAlchemy async) y Redis.
"""
from typing import AsyncGenerator
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase 
from sqlalchemy import text

from app.config import settings


# ── SQLAlchemy ────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection: sesión de base de datos por request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Redis ─────────────────────────────────────────────────────────────────────
redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Dependency injection: cliente Redis."""
    return redis_client


async def init_db():
    """Inicializar conexiones al arrancar la aplicación."""
    global redis_client
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Verificar conexión
    #await redis_client.ping()


async def close_db():
    """Cerrar conexiones al apagar la aplicación."""
    if redis_client:
        await redis_client.aclose()
    await engine.dispose()