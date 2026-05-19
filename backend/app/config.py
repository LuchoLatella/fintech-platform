"""
Configuración centralizada de la aplicación.
Todas las variables de entorno se leen desde aquí.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # ── Base de datos ─────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:5432/db
    REDIS_URL: str     # redis://:pass@host:6379/0
    CACHE_TTL_SECONDS: int = 300

    # ── APIs Financieras ──────────────────────────────────────────────────────
    ALPHA_VANTAGE_KEY: str = ""
    FINNHUB_KEY: str = ""
    POLYGON_KEY: str = ""
    TWELVE_DATA_KEY: str = ""
    IEX_CLOUD_KEY: str = ""
    FMP_KEY: str = ""
    BYMA_KEY: str = ""
    BYMA_SECRET: str = ""
    BINANCE_KEY: str = ""
    BINANCE_SECRET: str = ""

    # ── Notificaciones ────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""
    SENDGRID_KEY: str = ""
    FROM_EMAIL: str = "noreply@fintech.com"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""

    # ── Configuración de mercado ──────────────────────────────────────────────
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_TIMEFRAME: str = "1d"
    PRICE_FETCH_INTERVAL_SECONDS: int = 60
    SIGNAL_RECALC_INTERVAL_SECONDS: int = 300
    MAX_API_RETRIES: int = 3
    API_TIMEOUT_SECONDS: int = 10

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()