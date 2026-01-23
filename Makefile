ENV = .env.compose
BASE = docker-compose.yml
LOCAL = docker-compose-local.yml
PROD = docker-compose-prod.yml

COMPOSE_LOCAL = docker compose --env-file $(ENV) -f $(BASE) -f $(LOCAL)
COMPOSE_PROD = docker compose --env-file $(ENV) -f $(BASE) -f $(PROD)

# Development
local-up:
	$(COMPOSE_LOCAL) up --build -d

local-down:
	$(COMPOSE_LOCAL) down

local-clean-up:
	$(COMPOSE_LOCAL) down -v && make local-up

local-logs:
	$(COMPOSE_LOCAL) logs -f

local-logs-front:
	$(COMPOSE_LOCAL) logs -f frontend

local-logs-back:
	$(COMPOSE_LOCAL) logs -f backend

# Prod
prod-up:
	$(COMPOSE_PROD) up --build -d

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f

# Clear Docker Cache
system-prune:
	docker system prune -f