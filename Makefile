SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: help up down restart logs logs-api ps build seed-runbooks migrate test-alert clean

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

up: ## Build + start the full stack
	$(COMPOSE) up -d --build

down: ## Stop the stack (keep volumes)
	$(COMPOSE) down

restart: down up ## Restart everything

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

logs-api: ## Tail api logs only
	$(COMPOSE) logs -f api

ps: ## Show running services
	$(COMPOSE) ps

build: ## Rebuild images without starting
	$(COMPOSE) build

migrate: ## Apply Alembic migrations inside the api container
	$(COMPOSE) exec api alembic upgrade head

seed-runbooks: ## Re-index runbooks into ChromaDB (idempotent)
	$(COMPOSE) exec api python -m rag.indexer

test-alert: ## POST a sample alert and tail api logs
	@curl -sS -X POST http://localhost:8000/alerts \
		-H "Content-Type: application/json" \
		-d '{"device_id":"dev-storage-gw-042","alert_type":"connectivity_loss","severity_hint":"high","payload":{"last_seen":"2026-04-24T10:12:00Z","signal_strength":-92,"location":"warehouse-3"}}' \
		| python -m json.tool
	@echo "--- tailing api logs (Ctrl+C to exit) ---"
	$(COMPOSE) logs -f api

clean: ## Stop the stack and delete volumes (destroys data)
	$(COMPOSE) down -v
