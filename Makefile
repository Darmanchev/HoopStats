COMPOSE = docker compose \
	-p hoopstats-dev \
	--env-file .env

.PHONY: up down clean logs migrate seed seed-seasons seed-players train status

up:
	$(COMPOSE) up -d --build --remove-orphans

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) exec hoopstats-backend alembic upgrade head

seed:
	$(COMPOSE) exec hoopstats-backend python -m scripts.seed

seed-seasons:
	$(COMPOSE) exec hoopstats-backend python -m scripts.seed --seasons $(SEASONS)

seed-players:
	$(COMPOSE) exec hoopstats-backend python -m scripts.seed_player_season --season $(SEASON)

train:
	$(COMPOSE) exec hoopstats-backend python -m scripts.train_model

status:
	$(COMPOSE) ps
