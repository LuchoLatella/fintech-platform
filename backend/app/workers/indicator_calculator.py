"""
Worker: Indicator Calculator
Calcula indicadores técnicos y snapshots de portafolios.
"""
from celery import shared_task
import structlog

log = structlog.get_logger()

@shared_task(name="app.workers.indicator_calculator.calculate_all_indicators")
def calculate_all_indicators():
    log.info("indicator_calculator_placeholder")

@shared_task(name="app.workers.indicator_calculator.snapshot_all_portfolios")
def snapshot_all_portfolios():
    log.info("snapshot_portfolios_placeholder")