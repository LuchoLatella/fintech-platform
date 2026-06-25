from future import annotations

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import asyncio
import pandas as pd
import numpy as np
import httpx
import yfinance as yf

from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

import structlog

from app.core.config import settings

try:
    import redis.asyncio as redis
except Exception:
    redis = None

log = structlog.get_logger()


#DATA SOURCES--------------------------------------------------------------------------------------------------


class DataSource(str, Enum):
    ALPHAVANTAGE = "alphavantage"
    FINNHUB = "finnhub"
    YAHOO = "yahoo"


#PROVIDER ----------------------------------------------------------------------------------------------------


class MarketDataProvider:

    def __init__(self):

        self.alpha_key = settings.ALPHA_VANTAGE_KEY
        self.finnhub_key = settings.FINNHUB_KEY

        self.http = httpx.AsyncClient(
            timeout=20.0
        )

        self.memory_cache = TTLCache(
            maxsize=5000,
            ttl=300,
        )

        self.redis = None

        if redis:

            try:

                self.redis = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )

            except Exception as exc:

                log.warning(
                    "redis_init_failed",
                    error=str(exc),
                )

        self.quote_sources = [
            DataSource.ALPHAVANTAGE,
            DataSource.FINNHUB,
            DataSource.YAHOO,
        ]

        self.ohlcv_sources = [
            DataSource.ALPHAVANTAGE,
            DataSource.FINNHUB,
            DataSource.YAHOO,
        ]

        log.info(
            "market_provider_initialized",
            redis=bool(self.redis),
        )

