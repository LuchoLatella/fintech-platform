# =============================================================================
# FINTECH PLATFORM — Makefile
# Comandos útiles para desarrollo y operaciones
# =============================================================================

.PHONY: help up down logs shell db-shell redis-shell migrate seed test lint

help:
	@echo ""
	@echo "  Fintech Platform — Comandos disponibles"
	@echo ""
	@echo "  Infraestructura:"
	@echo "    make up          Levantar todos los servicios"
	@echo "    make down        Bajar todos los servicios"
	@echo "    make logs        Ver logs de todos los servicios"
	@echo "    make logs-api    Ver logs solo del backend"
	@echo ""
	@echo "  Base de datos:"
	@echo "    make migrate     Aplicar migraciones Alembic"
	@echo "    make migrate-gen Generar nueva migración"
	@echo "    make db-shell    Conectarse a PostgreSQL"
	@echo "    make seed        Cargar datos iniciales"
	@echo ""
	@echo "  Desarrollo:"
	@echo "    make shell       Shell dentro del contenedor API"
	@echo "    make test        Ejecutar tests"
	@echo "    make lint        Linting con ruff"
	@echo "    make redis-shell Conectarse a Redis"
	@echo "    make flower      Abrir monitor de Celery"
	@echo ""

# ── Infraestructura ───────────────────────────────────────────────────────────
up:
	docker compose up -d --build
	@echo "✓ Servicios levantados. API en http://localhost:8000/docs"

down:
	docker compose down

restart:
	docker compose restart api celery_worker celery_beat

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f celery_worker

# ── Base de datos ─────────────────────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migrate-gen:
	@read -p "Nombre de la migración: " name; \
	docker compose exec api alembic revision --autogenerate -m "$$name"

migrate-down:
	docker compose exec api alembic downgrade -1

db-shell:
	docker compose exec postgres psql -U $${POSTGRES_USER:-fintech} -d $${POSTGRES_DB:-fintech}

seed:
	docker compose exec api python -m app.scripts.seed_data

# ── Desarrollo ────────────────────────────────────────────────────────────────
shell:
	docker compose exec api bash

redis-shell:
	docker compose exec redis redis-cli -a $${REDIS_PASSWORD}

test:
	docker compose exec api pytest tests/ -v --tb=short

lint:
	docker compose exec api ruff check app/

flower:
	@echo "Flower disponible en http://localhost:5555"
	docker compose --profile dev up -d flower

# ── Operaciones ────────────────────────────────────────────────────────────────
fetch-prices:
	docker compose exec api celery -A app.workers.celery_app call app.workers.price_fetcher.fetch_all_watchlist_prices

gen-signals:
	docker compose exec api celery -A app.workers.celery_app call app.workers.signal_generator.generate_signals

fetch-argentina:
	docker compose exec api celery -A app.workers.celery_app call app.workers.price_fetcher.fetch_argentina_economic_data
