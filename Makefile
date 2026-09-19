COMPOSE = docker compose \
	-p hoopstats-dev \
	--env-file .env

.PHONY: up down clean logs migrate seed seed-seasons train status

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) exec backend alembic upgrade head

seed:
	$(COMPOSE) exec backend python -m scripts.seed

seed-seasons:
	$(COMPOSE) exec backend python -m scripts.seed --seasons $(SEASONS)

train:
	$(COMPOSE) exec backend python -m scripts.train_model

status:
	$(COMPOSE) ps
