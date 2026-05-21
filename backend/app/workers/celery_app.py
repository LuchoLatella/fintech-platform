"""
Celery App — Tareas asíncronas y programadas.
"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "fintech",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL.replace("/0", "/1"),
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL.replace("/0", "/2"),
    include=[
        "app.workers.price_fetcher",
        "app.workers.indicator_calculator",
        "app.workers.signal_generator",
        "app.workers.alert_checker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,
    task_track_started=True,
    task_soft_time_limit=120,  # 2 minutos por tarea
    task_time_limit=180,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# ── Schedule de tareas periódicas ─────────────────────────────────────────────
celery_app.conf.beat_schedule = {

    # Precios en tiempo real (mercado abierto)
    "fetch-prices-realtime": {
        "task": "app.workers.price_fetcher.fetch_all_watchlist_prices",
        "schedule": settings.PRICE_FETCH_INTERVAL_SECONDS,
    },

    # Precios de cripto (24/7)
    "fetch-crypto-prices": {
        "task": "app.workers.price_fetcher.fetch_crypto_prices",
        "schedule": 30,  # cada 30 segundos
    },

    # Datos económicos Argentina (cada hora en días hábiles)
    "fetch-argentina-data": {
        "task": "app.workers.price_fetcher.fetch_argentina_economic_data",
        "schedule": crontab(minute="0", hour="*/1"),
    },

    # Cálculo de indicadores técnicos
    "calculate-technical-indicators": {
        "task": "app.workers.indicator_calculator.calculate_all_indicators",
        "schedule": settings.SIGNAL_RECALC_INTERVAL_SECONDS,
    },

    # Generación de señales IA
    "generate-ai-signals": {
        "task": "app.workers.signal_generator.generate_signals",
        "schedule": crontab(minute="*/10"),  # cada 10 minutos
    },

    # Verificación de alertas de usuarios
    "check-user-alerts": {
        "task": "app.workers.alert_checker.check_all_alerts",
        "schedule": 60,  # cada minuto
    },

    # Datos fundamentales (diario, fuera de horario de mercado)
    "fetch-fundamental-data": {
        "task": "app.workers.price_fetcher.fetch_fundamental_data",
        "schedule": crontab(minute="0", hour="6"),  # 6 AM todos los días
    },

    # Snapshot de portafolios (fin del día)
    "snapshot-portfolios": {
        "task": "app.workers.indicator_calculator.snapshot_all_portfolios",
        "schedule": crontab(minute="30", hour="18", day_of_week="mon-fri"),
    },

    # Limpiar señales vencidas
    "cleanup-expired-signals": {
        "task": "app.workers.signal_generator.cleanup_expired_signals",
        "schedule": crontab(minute="0", hour="0"),  # medianoche
    },
}