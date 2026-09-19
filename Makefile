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
	$(COMPOSE) exec backend python seed.py

seed-seasons:
	$(COMPOSE) exec backend python seed.py --seasons $(SEASONS)

train:
	$(COMPOSE) exec backend python train_model.py

status:
	$(COMPOSE) ps
