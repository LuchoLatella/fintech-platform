"""
MarketDataProvider — capa de abstracción sobre múltiples APIs financieras.
Implementa fallback automático y validación cruzada de datos.
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum

import httpx
import yfinance as yf
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

import structlog
log = structlog.get_logger()


class DataSource(str, Enum):
    ALPHA_VANTAGE = "alphavantage"
    YAHOO_FINANCE = "yahoo"
    FINNHUB       = "finnhub"
    POLYGON       = "polygon"
    BYMA          = "byma"
    BINANCE       = "binance"


@dataclass
class Quote:
    symbol: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    source: DataSource
    currency: str = "USD"
    change_pct: Optional[float] = None


@dataclass
class OHLCV:
    symbol: str
    timeframe: str
    data: pd.DataFrame   # columnas: time, open, high, low, close, volume
    source: DataSource


class MarketDataProvider:
    """
    Proveedor unificado de datos de mercado.
    Intenta las fuentes en orden de prioridad y usa fallback automático.
    Cachea resultados en Redis para evitar duplicar requests.
    """

    # Orden de prioridad por tipo de activo
    PRIORITY: dict[str, list[DataSource]] = {
        "stock":  [DataSource.ALPHA_VANTAGE, DataSource.FINNHUB, DataSource.YAHOO_FINANCE],
        "etf":    [DataSource.YAHOO_FINANCE, DataSource.ALPHA_VANTAGE, DataSource.POLYGON],
        "crypto": [DataSource.BINANCE, DataSource.YAHOO_FINANCE],
        "cedear": [DataSource.BYMA, DataSource.YAHOO_FINANCE],
        "default":[DataSource.YAHOO_FINANCE, DataSource.ALPHA_VANTAGE, DataSource.FINNHUB],
    }

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._http = httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS)

    async def get_quote(self, symbol: str, asset_class: str = "default") -> Quote:
        """
        Obtiene la cotización actual con fallback automático entre fuentes.
        Cachea el resultado por 60 segundos en Redis.
        """
        cache_key = f"quote:{symbol}"

        # Intentar desde caché
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                import json
                data = json.loads(cached)
                return Quote(**data)

        sources = self.PRIORITY.get(asset_class, self.PRIORITY["default"])
        last_error = None

        for source in sources:
            try:
                quote = await self._fetch_quote(symbol, source)
                # Guardar en caché 60 segundos
                if self.redis:
                    import json
                    await self.redis.setex(cache_key, 60, json.dumps(quote.__dict__, default=str))
                log.info("quote_fetched", symbol=symbol, source=source.value)
                return quote
            except Exception as e:
                log.warning("quote_source_failed", symbol=symbol, source=source.value, error=str(e))
                last_error = e
                continue

        raise RuntimeError(f"Todas las fuentes fallaron para {symbol}: {last_error}")

    async def get_ohlcv(self, symbol: str, timeframe: str = "1d",
                         start: Optional[datetime] = None, end: Optional[datetime] = None,
                         asset_class: str = "default") -> OHLCV:
        """Obtiene datos OHLCV históricos con fallback."""
        #cache_key = f"ohlcv:{symbol}:{timeframe}"

        sources = self.PRIORITY.get(asset_class, self.PRIORITY["default"])

        for source in sources:
            try:
                return await self._fetch_ohlcv(symbol, timeframe, start, end, source)
            except Exception as e:
                log.warning("ohlcv_source_failed", symbol=symbol, source=source.value, error=str(e))
                continue

        raise RuntimeError(f"No se pudieron obtener datos OHLCV para {symbol}")

    # ── Implementaciones por fuente ────────────────────────────────────────────

    async def _fetch_quote(self, symbol: str, source: DataSource) -> Quote:
        if source == DataSource.YAHOO_FINANCE:
            return await self._quote_yahoo(symbol)
        elif source == DataSource.ALPHA_VANTAGE:
            return await self._quote_alpha_vantage(symbol)
        elif source == DataSource.FINNHUB:
            return await self._quote_finnhub(symbol)
        elif source == DataSource.BYMA:
            return await self._quote_byma(symbol)
        elif source == DataSource.BINANCE:
            return await self._quote_binance(symbol)
        raise NotImplementedError(f"Fuente no implementada: {source}")

    async def _fetch_ohlcv(self, symbol: str, timeframe: str,
                            start, end, source: DataSource) -> OHLCV:
        if source == DataSource.YAHOO_FINANCE:
            return await self._ohlcv_yahoo(symbol, timeframe, start, end)
        elif source == DataSource.ALPHA_VANTAGE:
            return await self._ohlcv_alpha_vantage(symbol, timeframe, start, end)
        raise NotImplementedError(f"OHLCV no implementado para: {source}")

    # ── Yahoo Finance ──────────────────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def _quote_yahoo(self, symbol: str) -> Quote:
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, lambda: yf.Ticker(symbol))
        info = await loop.run_in_executor(None, lambda: ticker.info)

        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        return Quote(
            symbol=symbol,
            price=price,
            open=info.get("regularMarketOpen", price),
            high=info.get("dayHigh", price),
            low=info.get("dayLow", price),
            close=info.get("previousClose", price),
            volume=info.get("regularMarketVolume", 0),
            timestamp=datetime.now(),
            source=DataSource.YAHOO_FINANCE,
            currency=info.get("currency", "USD"),
            change_pct=info.get("regularMarketChangePercent"),
        )

    async def _ohlcv_yahoo(self, symbol: str, timeframe: str, start, end) -> OHLCV:
        # Mapear timeframes internos a yfinance
        tf_map = {"1m":"1m","5m":"5m","15m":"15m","1h":"1h","4h":"1h","1d":"1d","1w":"1wk","1M":"1mo"}
        yf_period = tf_map.get(timeframe, "1d")

        loop = asyncio.get_event_loop()
        ticker = yf.Ticker(symbol)
        df = await loop.run_in_executor(None, lambda: ticker.history(
            period="1y" if not start else None,
            start=start, end=end,
            interval=yf_period,
        ))
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        df.index.name = "time"
        df = df.reset_index()

        return OHLCV(symbol=symbol, timeframe=timeframe, data=df, source=DataSource.YAHOO_FINANCE)

    # ── Alpha Vantage ──────────────────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
    async def _quote_alpha_vantage(self, symbol: str) -> Quote:
        url = "https://www.alphavantage.co/query"
        params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": settings.ALPHA_VANTAGE_KEY}
        r = await self._http.get(url, params=params)
        r.raise_for_status()
        data = r.json().get("Global Quote", {})
        price = float(data.get("05. price", 0))
        return Quote(
            symbol=symbol,
            price=price,
            open=float(data.get("02. open", price)),
            high=float(data.get("03. high", price)),
            low=float(data.get("04. low", price)),
            close=float(data.get("08. previous close", price)),
            volume=float(data.get("06. volume", 0)),
            timestamp=datetime.now(),
            source=DataSource.ALPHA_VANTAGE,
            change_pct=float(data.get("10. change percent", "0").replace("%", "")),
        )

    async def _ohlcv_alpha_vantage(self, symbol: str, timeframe: str, start, end) -> OHLCV:
        func_map = {"1d": "TIME_SERIES_DAILY", "1w": "TIME_SERIES_WEEKLY"}
        function = func_map.get(timeframe, "TIME_SERIES_DAILY")
        url = "https://www.alphavantage.co/query"
        params = {"function": function, "symbol": symbol, "outputsize": "full", "apikey": settings.ALPHA_VANTAGE_KEY}
        r = await self._http.get(url, params=params)
        r.raise_for_status()
        ts_key = [k for k in r.json() if "Time Series" in k][0]
        raw = r.json()[ts_key]
        rows = []
        for date_str, vals in raw.items():
            rows.append({
                "time": pd.Timestamp(date_str),
                "open": float(vals["1. open"]),
                "high": float(vals["2. high"]),
                "low": float(vals["3. low"]),
                "close": float(vals["4. close"]),
                "volume": float(vals["5. volume"]),
            })
        df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
        return OHLCV(symbol=symbol, timeframe=timeframe, data=df, source=DataSource.ALPHA_VANTAGE)

    # ── Finnhub ───────────────────────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def _quote_finnhub(self, symbol: str) -> Quote:
        url = f"https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol, "token": settings.FINNHUB_KEY}
        r = await self._http.get(url, params=params)
        r.raise_for_status()
        d = r.json()
        return Quote(
            symbol=symbol,
            price=d["c"],
            open=d["o"], high=d["h"], low=d["l"], close=d["pc"],
            volume=0,
            timestamp=datetime.fromtimestamp(d["t"]),
            source=DataSource.FINNHUB,
            change_pct=((d["c"] - d["pc"]) / d["pc"] * 100) if d["pc"] else None,
        )

    # ── BYMA (Argentina) ──────────────────────────────────────────────────────
    async def _quote_byma(self, symbol: str) -> Quote:
        """Endpoint público de BYMA para cotizaciones argentinas."""
        url = f"https://open.byma.com.ar/api/cotizaciones/{symbol}"
        headers = {"X-AUTH-TOKEN": settings.BYMA_KEY}
        r = await self._http.get(url, headers=headers)
        r.raise_for_status()
        d = r.json()
        return Quote(
            symbol=symbol,
            price=d.get("ultimoPrecio", 0),
            open=d.get("apertura", 0),
            high=d.get("maximo", 0),
            low=d.get("minimo", 0),
            close=d.get("cierreAnterior", 0),
            volume=d.get("cantidadNominal", 0),
            timestamp=datetime.now(),
            source=DataSource.BYMA,
            currency="ARS",
            change_pct=d.get("variacion"),
        )

    # ── Binance (Crypto) ──────────────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def _quote_binance(self, symbol: str) -> Quote:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {"symbol": symbol.replace("-", "").upper()}
        r = await self._http.get(url, params=params)
        r.raise_for_status()
        d = r.json()
        return Quote(
            symbol=symbol,
            price=float(d["lastPrice"]),
            open=float(d["openPrice"]),
            high=float(d["highPrice"]),
            low=float(d["lowPrice"]),
            close=float(d["prevClosePrice"]),
            volume=float(d["volume"]),
            timestamp=datetime.now(),
            source=DataSource.BINANCE,
            currency="USD",
            change_pct=float(d["priceChangePercent"]),
        )

    async def close(self):
        await self._http.aclose()