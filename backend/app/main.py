"""
FINTECH PLATFORM - API Principal
FastAPI app con CORS, middlewares, routers y WebSocket support
"""
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, market, analysis, signals, portfolio, alerts, argentina, websockets#, universe#, ml
from app.api.routes.auth import router as auth_router

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y cierre limpio de recursos."""
    log.info("startup", environment=settings.ENVIRONMENT)
    await init_db()
    yield
    await close_db()
    log.info("shutdown")


app = FastAPI(
    title="Fintech Intelligence Platform",
    description="Plataforma de análisis financiero e inteligencia de inversión",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ── Middlewares ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,       prefix=f"{API_PREFIX}/auth",      tags=["Autenticación"])
app.include_router(market.router,     prefix=f"{API_PREFIX}/market",     tags=["Mercado"])
app.include_router(analysis.router,   prefix=f"{API_PREFIX}/analysis",   tags=["Análisis"])
app.include_router(signals.router,    prefix=f"{API_PREFIX}/signals",    tags=["Señales IA"])
app.include_router(portfolio.router,  prefix=f"{API_PREFIX}/portfolio",  tags=["Portafolio"])
app.include_router(alerts.router,     prefix=f"{API_PREFIX}/alerts",     tags=["Alertas"])
app.include_router(argentina.router,  prefix=f"{API_PREFIX}/argentina",  tags=["Módulo Argentina"])
app.include_router(websockets.router, prefix="/ws/v1",                   tags=["WebSockets"])
#app.include_router(ml.router,         prefix=f"{API_PREFIX}/ml",         tags=["Machine Learning"])  
#app.include_router(universe.router,    prefix=f"{API_PREFIX}/universe",    tags=["Universo de Activos"])
app.include_router(auth_router,      prefix=f"{API_PREFIX}/auth",      tags=["Autenticación"])

@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "environment": settings.ENVIRONMENT}


@app.get("/", tags=["Sistema"])
async def root():
    return {
        "name": "Fintech Intelligence Platform API",
        "docs": "/docs",
        "disclaimer": (
            "Esta plataforma provee análisis y soporte informativo. "
            "No constituye asesoramiento financiero profesional. "
            "Toda inversión conlleva riesgo de pérdida de capital."
        )
    }