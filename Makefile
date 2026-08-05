.PHONY: help setup start build stop restart check fix clean test-api test-api-teardown seed

# Default target: display help information
help:
	@echo "=========================================================================="
	@echo "                      Plane Development Commands                         "
	@echo "=========================================================================="
	@echo "Development:"
	@echo "  make setup               - Run the setup script for configs and dependencies"
	@echo "  make start               - Spin up docker containers and start frontend servers"
	@echo "  make stop                - Stop and down the docker dev containers"
	@echo "  make restart             - Restart the backend containers"
	@echo "  make build               - Build all packages and applications"
	@echo "  make clean               - Remove build files and node_modules"
	@echo "  make seed                - Seed the databases inside running API container"
	@echo ""
	@echo "Quality & Linting:"
	@echo "  make check               - Run typescript, formatting, and linting checks"
	@echo "  make fix                 - Run auto-fix for formatting and linting issues"
	@echo ""
	@echo "Testing (Docker):"
	@echo "  make test-api            - Run Django/pytest suite in isolated stack"
	@echo "  make test-api-teardown   - Tear down the testing docker containers & volumes"
	@echo "=========================================================================="

setup:
	@chmod +x ./setup.sh
	./setup.sh

start:
	docker compose -f docker-compose-local.yml up -d
	pnpm dev

stop:
	docker compose -f docker-compose-local.yml down

restart:
	docker compose -f docker-compose-local.yml down
	docker compose -f docker-compose-local.yml up -d

build:
	pnpm build

clean:
	pnpm clean

check:
	pnpm check

fix:
	pnpm fix

test-api:
	docker compose -f docker-compose-test.yml up --build --abort-on-container-exit --exit-code-from api-tests

test-api-teardown:
	docker compose -f docker-compose-test.yml down -v

seed:
	docker compose -f docker-compose-local.yml exec api python manage.py seed_vj_startups
