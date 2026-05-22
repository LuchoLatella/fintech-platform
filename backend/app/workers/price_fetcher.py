"""
Worker: Price Fetcher
Tareas Celery para obtener precios, datos fundamentales y datos de Argentina.
"""
import asyncio
from datetime import datetime

import structlog
from celery import shared_task

log = structlog.get_logger()


@shared_task(name="app.workers.price_fetcher.fetch_all_watchlist_prices", bind=True, max_retries=2)
def fetch_all_watchlist_prices(self):
    """Actualiza precios de todos los activos en watchlists activas."""
    try:
        asyncio.get_event_loop().run_until_complete(_fetch_prices_async())
    except Exception as exc:
        log.error("price_fetch_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=15)


@shared_task(name="app.workers.price_fetcher.fetch_crypto_prices")
def fetch_crypto_prices():
    asyncio.get_event_loop().run_until_complete(_fetch_crypto_async())


@shared_task(name="app.workers.price_fetcher.fetch_argentina_economic_data")
def fetch_argentina_economic_data():
    asyncio.get_event_loop().run_until_complete(_fetch_argentina_async())


@shared_task(name="app.workers.price_fetcher.fetch_fundamental_data")
def fetch_fundamental_data():
    asyncio.get_event_loop().run_until_complete(_fetch_fundamental_async())


@shared_task(name="app.workers.price_fetcher.snapshot_all_portfolios")
def snapshot_all_portfolios():
    asyncio.get_event_loop().run_until_complete(_snapshot_portfolios_async())


# ── Implementaciones async ────────────────────────────────────────────────────
async def _fetch_prices_async():
    """Obtiene y guarda precios de activos en watchlists activas."""
    from app.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.services.market_data.provider import MarketDataProvider
    from sqlalchemy import select, text

    provider = MarketDataProvider()

    async with AsyncSessionLocal() as db:
        # Obtener activos únicos en watchlists
        result = await db.execute(
            text("""
                SELECT DISTINCT a.id, a.symbol, ac.code as asset_class
                FROM watchlist_items wi
                JOIN assets a ON wi.asset_id = a.id
                JOIN asset_classes ac ON a.asset_class_id = ac.id
                WHERE a.is_active = TRUE AND ac.code != 'crypto'
                LIMIT 150
            """)
        )
        assets = result.fetchall()
        log.info("fetching_prices", count=len(assets))

        saved = 0
        for asset_id, symbol, asset_class in assets:
            try:
                ohlcv = await provider.get_ohlcv(symbol, "1d", asset_class=asset_class)
                if ohlcv.data.empty:
                    continue

                # Guardar las últimas 2 velas en TimescaleDB
                recent = ohlcv.data.tail(2)
                for _, row in recent.iterrows():
                    await db.execute(
                        text("""
                            INSERT INTO price_ohlcv (time, asset_id, open, high, low, close, volume, source, timeframe)
                            VALUES (:time, :asset_id, :open, :high, :low, :close, :volume, :source, '1d')
                            ON CONFLICT (time, asset_id, timeframe) DO UPDATE
                            SET close = EXCLUDED.close, volume = EXCLUDED.volume
                        """),
                        {
                            "time": row["time"],
                            "asset_id": str(asset_id),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row.get("volume", 0)),
                            "source": ohlcv.source.value,
                        }
                    )
                saved += 1
            except Exception as e:
                log.warning("price_save_failed", symbol=symbol, error=str(e))
                continue

        await db.commit()
        log.info("prices_saved", count=saved)

    await provider.close()


async def _fetch_crypto_async():
    """Precios de criptomonedas (24/7 desde Binance)."""
    from app.database import AsyncSessionLocal
    from app.services.market_data.provider import MarketDataProvider, DataSource
    from sqlalchemy import text

    CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]
    provider = MarketDataProvider()

    async with AsyncSessionLocal() as db:
        for symbol in CRYPTO_SYMBOLS:
            try:
                quote = await provider._quote_binance(symbol)
                await db.execute(
                    text("""
                        INSERT INTO price_ticks (time, asset_id, price, source)
                        SELECT NOW(), id, :price, 'binance'
                        FROM assets WHERE symbol = :symbol AND is_active = TRUE
                        ON CONFLICT DO NOTHING
                    """),
                    {"price": quote.price, "symbol": symbol}
                )
            except Exception as e:
                log.warning("crypto_fetch_failed", symbol=symbol, error=str(e))
        await db.commit()

    await provider.close()


async def _fetch_argentina_async():
    """Datos económicos argentinos: dólar, riesgo país, inflación."""
    from app.database import AsyncSessionLocal
    from app.services.argentina.dolar import ArgentinaService
    from sqlalchemy import text

    svc = ArgentinaService()
    async with AsyncSessionLocal() as db:
        try:
            rates = await svc.get_dolar_rates()
            indicators = [
                ("dolar_oficial",   rates.oficial,    "ARS"),
                ("dolar_mep",       rates.mep,        "ARS"),
                ("dolar_ccl",       rates.ccl,        "ARS"),
                ("dolar_blue",      rates.blue,       "ARS"),
                ("dolar_tarjeta",   rates.tarjeta,    "ARS"),
            ]
            for code, value, unit in indicators:
                if value:
                    await db.execute(
                        text("""
                            INSERT INTO arg_economic_indicators (indicator_code, indicator_name, value, unit, period, source)
                            VALUES (:code, :code, :value, :unit, CURRENT_DATE, 'bcra_ambito')
                        """),
                        {"code": code, "value": value, "unit": unit}
                    )
        except Exception as e:
            log.error("argentina_fetch_failed", error=str(e))

        try:
            bcra = await svc.get_bcra_data()
            bcra_indicators = [
                ("tasa_politica_monetaria",  bcra.tasa_politica_monetaria, "%"),
                ("inflacion_mensual",         bcra.inflacion_mensual,       "%"),
                ("inflacion_interanual",      bcra.inflacion_interanual,    "%"),
                ("reservas_bcra_usd",         bcra.reservas_usd_mm,        "USD_MM"),
            ]
            for code, value, unit in bcra_indicators:
                if value:
                    await db.execute(
                        text("""
                            INSERT INTO arg_economic_indicators (indicator_code, indicator_name, value, unit, period, source)
                            VALUES (:code, :code, :value, :unit, CURRENT_DATE, 'bcra')
                        """),
                        {"code": code, "value": value, "unit": unit}
                    )
        except Exception as e:
            log.warning("bcra_save_failed", error=str(e))

        await db.commit()

        # Refrescar vista materializada
        try:
            await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY arg_latest_indicators"))
            await db.commit()
        except Exception:
            pass

    await svc.close()


async def _fetch_fundamental_async():
    """Obtiene datos fundamentales desde Financial Modeling Prep."""
    from app.database import AsyncSessionLocal
    from app.config import settings
    from sqlalchemy import text, select
    import httpx

    if not settings.FMP_KEY:
        log.warning("fmp_key_not_configured")
        return

    async with AsyncSessionLocal() as db:
        # Activos de tipo stock o etf
        result = await db.execute(
            text("SELECT a.id, a.symbol FROM assets a JOIN asset_classes ac ON a.asset_class_id = ac.id WHERE ac.code IN ('stock','etf') AND a.is_active = TRUE LIMIT 50")
        )
        assets = result.fetchall()

    async with httpx.AsyncClient(timeout=15) as http:
        async with AsyncSessionLocal() as db:
            for asset_id, symbol in assets:
                try:
                    url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{symbol}?apikey={settings.FMP_KEY}"
                    r = await http.get(url)
                    r.raise_for_status()
                    data = r.json()
                    if not data:
                        continue
                    d = data[0]
                    await db.execute(
                        text("""
                            INSERT INTO fundamental_data
                                (asset_id, period, period_type, pe_ratio, pb_ratio, roe, roa,
                                 debt_to_equity, dividend_yield, revenue_growth_yoy, source)
                            VALUES
                                (:asset_id, CURRENT_DATE, 'TTM', :pe, :pb, :roe, :roa,
                                 :dte, :dy, :rg, 'fmp')
                            ON CONFLICT (asset_id, period, period_type) DO UPDATE
                            SET pe_ratio=EXCLUDED.pe_ratio, pb_ratio=EXCLUDED.pb_ratio,
                                roe=EXCLUDED.roe, debt_to_equity=EXCLUDED.debt_to_equity
                        """),
                        {
                            "asset_id": str(asset_id),
                            "pe": d.get("peRatioTTM"),
                            "pb": d.get("priceToBookRatioTTM"),
                            "roe": d.get("returnOnEquityTTM"),
                            "roa": d.get("returnOnAssetsTTM"),
                            "dte": d.get("debtEquityRatioTTM"),
                            "dy": d.get("dividendYieldTTM"),
                            "rg": d.get("revenueGrowthTTM"),
                        }
                    )
                except Exception as e:
                    log.warning("fundamental_failed", symbol=symbol, error=str(e))
            await db.commit()
    log.info("fundamental_data_updated")


async def _snapshot_portfolios_async():
    """Crea snapshots diarios de todos los portafolios."""
    from app.database import AsyncSessionLocal
    from app.models.portfolio import Portfolio, PortfolioPosition, PortfolioSnapshot
    from app.services.market_data.provider import MarketDataProvider
    from app.models.asset import Asset
    from sqlalchemy import select
    from datetime import date

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Portfolio))
        portfolios = result.scalars().all()

    provider = MarketDataProvider()

    async with AsyncSessionLocal() as db:
        for portfolio in portfolios:
            try:
                pos_result = await db.execute(
                    select(PortfolioPosition, Asset)
                    .join(Asset, PortfolioPosition.asset_id == Asset.id)
                    .where(PortfolioPosition.portfolio_id == portfolio.id, PortfolioPosition.is_open == True)
                )
                rows = pos_result.all()
                total = 0.0
                positions_snapshot = []
                for pos, asset in rows:
                    try:
                        quote = await provider.get_quote(asset.symbol)
                        mv = float(pos.quantity) * quote.price
                        total += mv
                        positions_snapshot.append({"symbol": asset.symbol, "market_value": mv, "quantity": float(pos.quantity)})
                    except:
                        pass

                snapshot = PortfolioSnapshot(
                    portfolio_id=portfolio.id,
                    snapshot_date=date.today(),
                    total_value_usd=total,
                    positions_data={"positions": positions_snapshot},
                )
                db.add(snapshot)
            except Exception as e:
                log.warning("snapshot_failed", portfolio_id=str(portfolio.id), error=str(e))

        await db.commit()

    await provider.close()
    log.info("portfolio_snapshots_created", count=len(portfolios))