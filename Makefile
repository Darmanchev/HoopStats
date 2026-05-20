.PHONY: up down build rebuild logs seed sync shell db-logs backend-logs frontend-logs restart migrate

# Docker Compose
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

restart:
	docker compose restart

# Logs
logs:
	docker compose logs -f

backend-logs:
	docker compose logs -f backend

frontend-logs:
	docker compose logs -f frontend

db-logs:
	docker compose logs -f db

# Database
migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python seed.py

sync:
	docker compose exec backend python seed.py

# Shell access
shell:
	docker compose exec backend sh

db-shell:
	docker compose exec db psql -U admin -d hoopstats

# Status
status:
	docker compose ps

# Clean
clean:
	docker compose down -v
	rm -rf data/postgres/*
