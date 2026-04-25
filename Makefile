.PHONY: setup data-pull data-push up down clean help

# Default
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Setup ---
setup: ## Full student setup: submodule + data + docker + uv
	@echo ">>> Init submodules"
	git submodule update --init --recursive
	@echo ">>> Pull data from R2"
	$(MAKE) data-pull
	@echo ">>> Docker stack"
	$(MAKE) up
	@echo ">>> Python deps"
	uv sync
	@echo ">>> Setup your EPCI: python scripts/00_setup.py --epci \"<votre EPCI>\""

# --- Data (R2) ---
data-pull: ## Pull data from Cloudflare R2
	@test -f rclone.conf || (echo "Missing rclone.conf — copy rclone.conf.example and fill credentials" && exit 1)
	./scripts/data_pull.sh

data-push: ## Push data to Cloudflare R2 (instructor only)
	@test -f rclone.conf || (echo "Missing rclone.conf" && exit 1)
	./scripts/data_push.sh

# --- Docker ---
up: ## Start PostGIS + Neo4j
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")
	docker compose up -d

down: ## Stop all containers
	docker compose down

restart: down up ## Restart all containers

# --- Cleanup ---
clean: ## Stop docker + remove volumes
	docker compose down -v
