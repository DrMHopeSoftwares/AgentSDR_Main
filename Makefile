.PHONY: help install dev test lint clean seed docker-build docker-run docker-stop

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	pip install -r requirements.txt

dev: ## Run development server
	FLASK_ENV=development python app.py

test: ## Run tests with coverage
	pytest tests/ -v --cov=agentsdr --cov-report=html --cov-report=term

lint: ## Run linting and formatting
	black agentsdr/ tests/ --check
	ruff check agentsdr/ tests/

format: ## Format code
	black agentsdr/ tests/
	ruff check --fix agentsdr/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/
	rm -rf .pytest_cache/

seed: ## Seed database with demo data
	python scripts/seed.py

docker-build: ## Build Docker image
	docker-compose build

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

setup: ## Initial setup
	@echo "Setting up AgentSDR..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "Please update .env with your Supabase credentials"; \
	fi
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Setup complete! Update .env and run 'make dev' to start"

deploy-check: ## Check deployment readiness
	@echo "Checking deployment requirements..."
	@python -c "import os; from dotenv import load_dotenv; load_dotenv(); \
		required = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY', 'FLASK_SECRET_KEY']; \
		missing = [k for k in required if not os.getenv(k)]; \
		print('Missing environment variables:', missing) if missing else print('✅ All required env vars set')"
