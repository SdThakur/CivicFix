# CivicFix Makefile

.PHONY: dev build seed test lint docker-up docker-down migrate

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up --build

docker-down:
	docker compose down -v

# ── Backend ───────────────────────────────────────────────────────────────────
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

worker:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info -Q reports,analytics,emails

beat:
	cd backend && celery -A app.workers.celery_app beat --loglevel=info

# ── Frontend ──────────────────────────────────────────────────────────────────
dev-frontend:
	cd frontend && npm run dev

install-frontend:
	cd frontend && npm install

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed:
	cd backend && python scripts/seed.py

create-admin:
	cd backend && python scripts/create_admin.py

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-unit:
	cd backend && pytest tests/unit/ -v

test-api:
	cd backend && pytest tests/api/ -v

test-integration:
	cd backend && pytest tests/integration/ -v

# ── Code Quality ──────────────────────────────────────────────────────────────
lint:
	cd backend && python -m flake8 app/ --max-line-length=120 --exclude=__pycache__
