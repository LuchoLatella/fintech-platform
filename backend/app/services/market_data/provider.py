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

# CACHE MAS QUOTES --------------------------------------------------------------------------------------------------

async def _get_cache(self, key: str):

    try: 
        
        if key in self.memory_cache: 
            return self.memory_cache[key]
    
    except Exception: pass

    if self.redis:

        try:

            value = await self.redis.get(key)

            if value is not None:

                try: value = float(value) 
                except Exception: pass 
                self.memory_cache[key] = value

                return value

        except Exception as exc:

            log.warning(
                "redis_cache_failed",
                error=str(exc),
                key=key,
            )

    # if key in self.memory_cache:
    #     return self.memory_cache[key]

    return None

async def _set_cache(
self,
key: str,
value,
ttl: int = 300,
):

    try:
        self.memory_cache[key] = value
    except Exception:
        pass

    if self.redis:

        try:

            await self.redis.set(
                key,
                value,
                ex=ttl,
            )

        except Exception as exc:

            log.warning(
                "redis_cache_failed",
                error=str(exc),
                key=key,
            )

# QUOTES --------------------------------------------------------------------------------------------------

async def get_quote(
self,
symbol: str,
) -> Optional[float]:
    
    symbol = symbol.upper()

    cache_key = f"quote:{symbol}"

    cached = await self._get_cache(cache_key)

    if cached is not None:
        log.debug(
            "quote_cache_hit",
            symbol=symbol,
        )

        return float(cached)
    
    for source in self.quote_sources:
        try:
            log.info(
                "trying_source", 
                source=source.value, 
                symbol=symbol,
            )

            if source == DataSource.ALPHAVANTAGE:
                price = await self._get_quote_alphavantage( symbol ) 

            elif source == DataSource.FINNHUB:
                price = await self._get_quote_finnhub( symbol )

            else:
                price = await self._get_quote_yahoo( symbol )

            if price and price > 0:

                await self._set_cache(
                    cache_key,
                    price,
                    ttl=300,
                )

                log.info(
                    "quote_ok",
                    symbol=symbol,
                    source=source.value,
                    price=price,
                )

                return float(price)
        
        except Exception as exc:
        
            log.warning(
                "quote_source_failed",
                source=source.value,
                symbol=symbol,
                error=str(exc),
            )
    return None

# ALPHAVANTAGE QUOTE --------------------------------------------------------------------------------------------------

async def _get_quote_alphavantage(
self,
symbol: str,
) -> Optional[float]:

    url = ( "https://www.alphavantage.co/query" "?function=GLOBAL_QUOTE" f"&symbol={symbol}" f"&apikey={self.alpha_key}" )

    response = await self.http.get(url) 
    response.raise_for_status() 
    data = response.json() 
    quote = data.get("Global Quote")

    if not quote:
        return None
    return float(quote["05. price"])

# FINNHUB QUOTE --------------------------------------------------------------------------------------------------

async def _get_quote_finnhub(
self,
symbol: str,
) -> Optional[float]:

    url = ( "https://finnhub.io/api/v1/quote" f"?symbol={symbol}" f"&token={self.finnhub_key}" )

    response = await self.http.get(url)
    response.raise_for_status()
    data = response.json()
    price = data.get("c")

    if not price:
        return None
    return float(price)

# YAHOO QUOTE --------------------------------------------------------------------------------------------------

@retry(
stop=stop_after_attempt(3),
wait=wait_exponential(
multiplier=1,
min=1,
max=5,
),
)
async def _get_quote_yahoo(
self,
symbol: str,
) -> Optional[float]:
    
    ticker = yf.Ticker(symbol)

    info = ticker.fast_info

    price = info.get("lastPrice")

    if price is None:
        return None
    return float(price)

