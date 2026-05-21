"""
Router: Módulo Argentina
Endpoints para datos económicos y de mercado argentino.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import redis.asyncio as aioredis

from app.database import get_redis
from app.services.argentina.dolar import ArgentinaService, DolarRates, ArgentineMarketSnapshot

router = APIRouter()


class DolarResponse(BaseModel):
    oficial: Optional[float]
    mayorista: Optional[float]
    mep: Optional[float]
    ccl: Optional[float]
    blue: Optional[float]
    crypto: Optional[float]
    tarjeta: Optional[float]
    spread_mep_oficial: Optional[float]
    spread_ccl_mep: Optional[float]
    timestamp: Optional[str]

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    dolar: DolarResponse
    riesgo_pais: float
    inflacion_mensual: Optional[float]
    inflacion_interanual: Optional[float]
    tasa_politica_monetaria: Optional[float]
    reservas_usd_mm: Optional[float]
    opportunities: list[dict]
    generated_at: str

    class Config:
        from_attributes = True


async def get_argentina_service(redis: aioredis.Redis = Depends(get_redis)) -> ArgentinaService:
    from app.config import settings
    return ArgentinaService(redis_client=redis, byma_key=settings.BYMA_KEY)


@router.get("/dolar", response_model=DolarResponse, summary="Tipos de cambio ARS/USD")
async def get_dolar(service: ArgentinaService = Depends(get_argentina_service)):
    """
    Retorna todos los tipos de cambio: oficial, mayorista, MEP, CCL, blue, crypto, tarjeta.
    Cachea por 2 minutos. Fuentes: BCRA + Ámbito.
    """
    try:
        rates = await service.get_dolar_rates()
        return DolarResponse(
            oficial=rates.oficial,
            mayorista=rates.mayorista,
            mep=rates.mep,
            ccl=rates.ccl,
            blue=rates.blue,
            crypto=rates.crypto,
            tarjeta=rates.tarjeta,
            spread_mep_oficial=rates.spread_mep_oficial,
            spread_ccl_mep=rates.spread_ccl_mep,
            timestamp=str(rates.timestamp) if rates.timestamp else None,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error al obtener cotizaciones: {str(e)}")


@router.get("/snapshot", response_model=SnapshotResponse, summary="Snapshot completo del mercado ARG")
async def get_snapshot(service: ArgentinaService = Depends(get_argentina_service)):
    """
    Snapshot completo: dólar + BCRA + riesgo país + oportunidades detectadas.
    Ideal para el panel principal del módulo Argentina.
    """
    try:
        snapshot = await service.get_market_snapshot()
        opportunities = await service.detect_opportunities(snapshot.dolar)

        return SnapshotResponse(
            dolar=DolarResponse(
                oficial=snapshot.dolar.oficial,
                mayorista=snapshot.dolar.mayorista,
                mep=snapshot.dolar.mep,
                ccl=snapshot.dolar.ccl,
                blue=snapshot.dolar.blue,
                crypto=snapshot.dolar.crypto,
                tarjeta=snapshot.dolar.tarjeta,
                spread_mep_oficial=snapshot.dolar.spread_mep_oficial,
                spread_ccl_mep=snapshot.dolar.spread_ccl_mep,
                timestamp=str(snapshot.dolar.timestamp),
            ),
            riesgo_pais=snapshot.riesgo_pais.value if snapshot.riesgo_pais else 0,
            inflacion_mensual=snapshot.bcra.inflacion_mensual,
            inflacion_interanual=snapshot.bcra.inflacion_interanual,
            tasa_politica_monetaria=snapshot.bcra.tasa_politica_monetaria,
            reservas_usd_mm=snapshot.bcra.reservas_usd_mm,
            opportunities=opportunities,
            generated_at=str(snapshot.generated_at),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error al generar snapshot: {str(e)}")


@router.get("/riesgo-pais", summary="Riesgo país (EMBI+)")
async def get_riesgo_pais(service: ArgentinaService = Depends(get_argentina_service)):
    """Retorna el riesgo país (spread EMBI+ en basis points)."""
    try:
        rp = await service.get_riesgo_pais()
        return {"value": rp.value, "unit": "bps", "updated_at": str(rp.updated_at)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/bcra", summary="Datos del Banco Central")
async def get_bcra(service: ArgentinaService = Depends(get_argentina_service)):
    """Reservas, tasas e inflación del BCRA."""
    try:
        bcra = await service.get_bcra_data()
        return {
            "reservas_usd_mm": bcra.reservas_usd_mm,
            "base_monetaria_mm": bcra.base_monetaria_mm,
            "tasa_politica_monetaria": bcra.tasa_politica_monetaria,
            "inflacion_mensual": bcra.inflacion_mensual,
            "inflacion_interanual": bcra.inflacion_interanual,
            "updated_at": str(bcra.updated_at),
            "source": "BCRA API (api.bcra.gob.ar)",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/oportunidades", summary="Oportunidades detectadas en mercado ARG")
async def get_opportunities(service: ArgentinaService = Depends(get_argentina_service)):
    """
    Detecta oportunidades de arbitraje y estrategias específicas del mercado argentino:
    - Arbitraje MEP/CCL
    - CEDEARs subvaluados respecto al subyacente
    - Bonos soberanos con spread atractivo
    """
    try:
        rates = await service.get_dolar_rates()
        opportunities = await service.detect_opportunities(rates)
        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "disclaimer": "Análisis informativo. No constituye asesoramiento financiero.",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))