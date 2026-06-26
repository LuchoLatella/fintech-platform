from __future__ import annotations

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

from app.config import settings

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

    def __init__(
        self,
        redis_client=None,
        alpha_key=None,
        finnhub_key=None,
    ):

        self.redis = redis_client

        self.alpha_key = alpha_key or settings.ALPHA_VANTAGE_KEY
        self.finnhub_key = finnhub_key or settings.FINNHUB_KEY

        self.http = httpx.AsyncClient(
            timeout=20,
            headers={
                "User-Agent": "FintechPlatform/1.0"
            }
        )

        if self.redis is None:
            try:
                self.redis = redis.from_url(settings.REDIS_URL)
            except Exception:
                self.redis = None

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

        response = self.http.get(url) 
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

        response = self.http.get(url)
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

# OHLCV --------------------------------------------------------------------------------------------------

    async def get_ohlcv(
        self,
        symbol: str,
        period: str = "1y",
        ) -> pd.DataFrame:
    
        symbol = symbol.upper() 
        cache_key = f"ohlcv:{symbol}:{period}" 
        cached = await self._get_cache(cache_key)

        if isinstance(cached, pd.DataFrame):
            return cached

        for source in self.ohlcv_sources:
            try:
                log.info( 
                    "ohlcv_try", 
                    symbol=symbol, 
                    source=source.value,
                )

                if source == DataSource.ALPHAVANTAGE:
                    df = await self._get_ohlcv_alphavantage(symbol)
        
                elif source == DataSource.FINNHUB:
                    df = await self._get_ohlcv_finnhub(symbol)

                else:
                    df = await self._get_ohlcv_yahoo(symbol)

                if not df.empty:

                    await self._set_cache( cache_key, df, ttl=3600, )

                    log.info( "ohlcv_ok", symbol=symbol, source=source.value, rows=len(df), )

                    return df
    
            except Exception as exc:
        
                log.warning(
                    "ohlcv_source_failed",
                    symbol=symbol,
                    source=source.value,
                    error=str(exc),
                )

        return pd.DataFrame()

# ALPHAVANTAGE OHLCV --------------------------------------------------------------------------------------------------

    async def _get_ohlcv_alphavantage(
    self,
    symbol: str,
    ) -> pd.DataFrame:
    
        url = ( "https://www.alphavantage.co/query" "?function=TIME_SERIES_DAILY_ADJUSTED" f"&symbol={symbol}" "&outputsize=full" f"&apikey={self.alpha_key}" )

        response = self.http.get(url)

        response.raise_for_status()

        data = response.json()

        ts = data.get( "Time Series (Daily)" )

        if not ts:

            raise ValueError(f"No Time Series encontrada. Respuesta: {data}")
    
        rows = []

        for date_str, values in ts.items():

            rows.append(
                {
                    "time": pd.to_datetime(date_str), 
                    "open": float(values["1. open"]), 
                    "high": float(values["2. high"]), 
                    "low": float(values["3. low"]), 
                    "close": float(values["4. close"]), 
                    "volume": float(values["6. volume"]), 
                }
            )  
    
        df = pd.DataFrame(rows)

        df.sort_values( "time", inplace=True, )
        df.set_index( "time", inplace=True, )

        return df

# FINNHUB OHLCV --------------------------------------------------------------------------------------------------

    async def _get_ohlcv_finnhub(self,
    symbol: str,
    ) -> pd.DataFrame:
    
        end = int(datetime.utcnow().timestamp())

        start = int( ( datetime.utcnow() - timedelta(days=365) ).timestamp() )

        url = ( "https://finnhub.io/api/v1/stock/candle" f"?symbol={symbol}" "&resolution=D" f"&from={start}" f"&to={end}" f"&token={self.finnhub_key}" )

        response = self.http.get(url) 
        response.raise_for_status() 
        data = response.json()

        if data.get("s") != "ok":   
            raise ValueError(f"No se pudo obtener OHLCV de Finnhub. Respuesta: {data}")
    
        df = pd.DataFrame(
            {
            "time": pd.to_datetime(data["t"], unit="s"), 
            "open": data["o"], 
            "high": data["h"], 
            "low": data["l"], 
            "close": data["c"], 
            "volume": data["v"], 
            }
        )

        df.set_index("time", inplace=True)

        return df

# YAHOO OHLCV --------------------------------------------------------------------------------------------------

    async def _get_ohlcv_yahoo(self,
    symbol: str,
    period: str = "1y",
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)

        df = ticker.history( period=period, auto_adjust=True, )

        if df.empty:
            raise ValueError(f"No se pudo obtener OHLCV de Yahoo Finance para {symbol}")
    
        df = df.rename( columns={ "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume", } )

        df.index.name = "time"

        return df[ [ "open", "high", "low", "close", "volume", ] ]



# BENCHMARK --------------------------------------------------------------------------------------------------

    async def get_benchmark_returns(
        self,
        benchmark: str = "SPY",
    ) -> pd.Series:
        try:
            df = await self.get_ohlcv(benchmark, "1y")

            if df.empty:
                return pd.Series(dtype=float)

            returns = df["close"].pct_change().dropna()

            log.info("benchmark_ok", benchmark=benchmark, rows=len(returns))

            return returns
        except Exception as exc:
            log.warning("benchmark_failed", benchmark=benchmark, error=str(exc))
            return pd.Series(dtype=float)
    

    # CURRENT PRICE--------------------------------------------------------------------------------------------------

    async def get_current_price(
    self,
    symbol: str,
    ) -> Optional[float]:

        quote = await self.get_quote(symbol)

        if not quote:
            return None
        return quote.price

# NORMALIZACION --------------------------------------------------------------------------------------------------

    def normalize_symbol(
    self,
    symbol: str,
    ) -> str:
    
        symbol = symbol.upper().strip()

        replacements = { ".BA": "", " US": "", "NYSE:": "", "NASDAQ:": "", }

        for old, new in replacements.items():
            symbol = symbol.replace(old, new)

        return symbol

# VALIDACION --------------------------------------------------------------------------------------------------

    async def is_valid_price(
    self,
    value: Any,
    ) -> bool:
    
        try: return ( value is not None and float(value) > 0 )

        except Exception: return False


# REDIS --------------------------------------------------------------------------------------------------

    async def ping_redis(self) -> bool:

        if not self.redis: return False

        try: 
        
            await self.redis.ping() 
    
            return True
    
        except Exception: 
            return False
    
# MARKET PROVIDER STATUS --------------------------------------------------------------------------------------------------

    async def health_check(self) -> Dict[str, Any]:

        redis_ok = await self.ping_redis()

        status = { "redis": redis_ok, 
              "alphavantage": bool(self.alpha_key), 
              "finnhub": bool(self.finnhub_key), 
              "yahoo": True, }
    
        status["overall"] = any([status["alphavantage"], status["finnhub"], status["yahoo"]])

        return status

# CLOSE RESOURCES --------------------------------------------------------------------------------------------------


    async def close(self):

        try: 
            if self.http: await self.http.aclose()

        except Exception as esc:

            log.warning( "http_close_failed", error=str(exc), )

        try: 
            if self.redis: 
                await self.redis.close()
    
        except Exception as exc:
            log.warning( "redis_close_failed", error=str(exc), )


# ASYNC CONTEXT SUPPORT --------------------------------------------------------------------------------------------------

    async def aenter(self):

        return self

    async def aexit(
        self,
        exc_type,
        exc,
        tb,
            ):

        await self.close()

# SINGLETON --------------------------------------------------------------------------------------------------

    _provider_instance = None

    def get_market_provider():

        global _provider_instance

        if _provider_instance is None:

            _provider_instance = MarketDataProvider()

        return _provider_instance


