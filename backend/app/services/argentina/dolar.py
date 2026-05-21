"""
Módulo Argentina — Servicio de datos económicos locales.
Fuentes: BCRA (API pública), BYMA, Ambito, Cronista.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

import structlog
log = structlog.get_logger()


@dataclass
class DolarRates:
    """Tipos de cambio ARS/USD"""
    oficial: Optional[float] = None
    mayorista: Optional[float] = None
    mep: Optional[float] = None           # Dólar Bolsa (GD30)
    ccl: Optional[float] = None           # Contado con Liqui
    blue: Optional[float] = None
    crypto: Optional[float] = None        # USDT en pesos
    tarjeta: Optional[float] = None       # Oficial + impuesto PAÍS + percepción
    timestamp: datetime = None

    @property
    def spread_mep_oficial(self) -> Optional[float]:
        if self.mep and self.oficial:
            return round((self.mep / self.oficial - 1) * 100, 2)
        return None

    @property
    def spread_ccl_mep(self) -> Optional[float]:
        if self.ccl and self.mep:
            return round((self.ccl / self.mep - 1) * 100, 2)
        return None


@dataclass
class BCRAData:
    """Datos principales del Banco Central"""
    reservas_usd_mm: Optional[float] = None    # reservas en millones USD
    base_monetaria_mm: Optional[float] = None
    tasa_politica_monetaria: Optional[float] = None  # %
    tasa_plazo_fijo_30d: Optional[float] = None
    inflacion_mensual: Optional[float] = None
    inflacion_interanual: Optional[float] = None
    updated_at: Optional[datetime] = None


@dataclass
class RiesgoPais:
    """EMBI+ Argentina (spread en basis points)"""
    value: float
    variation_daily: Optional[float] = None
    variation_ytd: Optional[float] = None
    updated_at: datetime = None


@dataclass
class ArgentineMarketSnapshot:
    """Snapshot completo del mercado argentino"""
    dolar: DolarRates
    bcra: BCRAData
    riesgo_pais: RiesgoPais
    merval: Optional[float] = None          # puntos
    merval_usd: Optional[float] = None      # en USD
    generated_at: datetime = None


class ArgentinaService:
    """
    Servicio de datos económicos y financieros argentinos.
    Agrega datos de BCRA (API pública), BYMA, Ambito y otras fuentes.
    """

    BCRA_BASE_URL = "https://api.bcra.gob.ar"
    AMBITO_DOLAR_URL = "https://mercados.ambito.com/dolar/{tipo}/variacion"
    BYMA_BASE_URL = "https://open.byma.com.ar/api"

    def __init__(self, redis_client=None, byma_key: str = ""):
        self.redis = redis_client
        self.byma_key = byma_key
        self._http = httpx.AsyncClient(timeout=15)

    async def get_market_snapshot(self) -> ArgentineMarketSnapshot:
        """Obtiene el snapshot completo del mercado argentino."""
        cache_key = "argentina:snapshot"

        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                import json
                # deserializar y retornar (simplificado)
                pass

        dolar, bcra, riesgo = await self._fetch_all_concurrent()

        snapshot = ArgentineMarketSnapshot(
            dolar=dolar,
            bcra=bcra,
            riesgo_pais=riesgo,
            generated_at=datetime.now(),
        )

        if self.redis:
            import json
            await self.redis.setex(cache_key, 120, json.dumps({
                "mep": dolar.mep, "ccl": dolar.ccl, "blue": dolar.blue,
                "riesgo_pais": riesgo.value if riesgo else None,
            }))

        return snapshot

    async def _fetch_all_concurrent(self):
        """Obtiene dólar, BCRA y riesgo país en paralelo."""
        import asyncio
        results = await asyncio.gather(
            self.get_dolar_rates(),
            self.get_bcra_data(),
            self.get_riesgo_pais(),
            return_exceptions=True,
        )
        dolar = results[0] if not isinstance(results[0], Exception) else DolarRates()
        bcra  = results[1] if not isinstance(results[1], Exception) else BCRAData()
        riesgo= results[2] if not isinstance(results[2], Exception) else RiesgoPais(value=0)
        return dolar, bcra, riesgo

    # ── Tipos de cambio ────────────────────────────────────────────────────────
    async def get_dolar_rates(self) -> DolarRates:
        """Obtiene todos los tipos de cambio ARS/USD."""
        rates = DolarRates(timestamp=datetime.now())

        try:
            # BCRA - tipo oficial
            bcra_data = await self._bcra_request("/estadisticas/v2.0/principalesvariables")
            for item in bcra_data.get("results", []):
                if item.get("idVariable") == 1:   # tipo de cambio minorista
                    rates.oficial = item.get("valor")
                elif item.get("idVariable") == 4: # tipo de cambio mayorista
                    rates.mayorista = item.get("valor")
                elif item.get("idVariable") == 5: # tasa plazo fijo
                    pass
        except Exception as e:
            log.warning("bcra_dolar_failed", error=str(e))

        # Dólar MEP, CCL y Blue desde fuentes alternativas
        try:
            mep_data = await self._ambito_request("mep")
            rates.mep = float(mep_data.get("venta", 0))
        except Exception as e:
            log.warning("mep_fetch_failed", error=str(e))

        try:
            ccl_data = await self._ambito_request("contadoconliqui")
            rates.ccl = float(ccl_data.get("venta", 0))
        except Exception as e:
            log.warning("ccl_fetch_failed", error=str(e))

        try:
            blue_data = await self._ambito_request("informal")
            rates.blue = float(blue_data.get("venta", 0))
        except Exception as e:
            log.warning("blue_fetch_failed", error=str(e))

        if rates.oficial:
            rates.tarjeta = round(rates.oficial * 1.60, 2)  # +60% impuestos (ajustar según normativa vigente)

        return rates

    # ── BCRA ───────────────────────────────────────────────────────────────────
    async def get_bcra_data(self) -> BCRAData:
        """Obtiene datos macroeconómicos del BCRA."""
        data = BCRAData(updated_at=datetime.now())
        try:
            variables = await self._bcra_request("/estadisticas/v2.0/principalesvariables")
            var_map = {item["idVariable"]: item.get("valor") for item in variables.get("results", [])}
            data.reservas_usd_mm           = var_map.get(1)
            data.base_monetaria_mm         = var_map.get(15)
            data.tasa_politica_monetaria   = var_map.get(7)
            data.inflacion_mensual         = var_map.get(27)
            data.inflacion_interanual      = var_map.get(28)
        except Exception as e:
            log.error("bcra_data_failed", error=str(e))
        return data

    async def get_riesgo_pais(self) -> RiesgoPais:
        """
        Riesgo país (EMBI+).
        Se calcula como el spread del bono GD30 vs Treasury 10y.
        Alternativa: endpoint de BCRA o scraping de ámbito.
        """
        try:
            # Variable 5 del BCRA suele incluir indicadores de deuda
            r = await self._http.get(f"{self.BCRA_BASE_URL}/estadisticas/v2.0/DatosVariable/5/2024-01-01/{datetime.now().strftime('%Y-%m-%d')}")
            r.raise_for_status()
            results = r.json().get("results", [])
            if results:
                latest = results[-1]
                return RiesgoPais(
                    value=latest.get("valor", 0),
                    updated_at=datetime.now(),
                )
        except Exception as e:
            log.warning("riesgo_pais_failed", error=str(e))

        # Fallback: valor por defecto (debería venir de otra fuente en prod)
        return RiesgoPais(value=0, updated_at=datetime.now())

    # ── Detección de oportunidades Argentina ───────────────────────────────────
    async def detect_opportunities(self, dolar: DolarRates) -> list[dict]:
        """
        Detecta oportunidades de arbitraje y estrategias específicas del mercado ARG.
        """
        opportunities = []

        # Oportunidad: spread MEP vs CCL > 3% → carry trade posible
        if dolar.spread_ccl_mep and dolar.spread_ccl_mep > 3:
            opportunities.append({
                "type": "dolar_arbitrage",
                "description": f"Spread CCL/MEP del {dolar.spread_ccl_mep:.1f}% — oportunidad de arbitraje cambiario",
                "confidence": min(dolar.spread_ccl_mep * 10, 90),
                "risk": "medium",
            })

        # Oportunidad: blue muy por encima del MEP → posible convergencia
        if dolar.blue and dolar.mep:
            spread_blue_mep = (dolar.blue / dolar.mep - 1) * 100
            if spread_blue_mep > 10:
                opportunities.append({
                    "type": "dolar_convergence",
                    "description": f"Spread blue/MEP del {spread_blue_mep:.1f}% — posible convergencia",
                    "confidence": 60,
                    "risk": "high",
                })

        return opportunities

    # ── Helpers HTTP ───────────────────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def _bcra_request(self, path: str) -> dict:
        r = await self._http.get(f"{self.BCRA_BASE_URL}{path}")
        r.raise_for_status()
        return r.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def _ambito_request(self, tipo: str) -> dict:
        url = self.AMBITO_DOLAR_URL.format(tipo=tipo)
        r = await self._http.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self._http.aclose()