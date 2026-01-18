.PHONY: help install dev test test-unit test-integration test-contract coverage lint format typecheck clean docker-build docker-run docker-test pre-commit

# Default target
help:
	@echo "Sovereign AI Platform - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make dev            Install development dependencies"
	@echo "  make pre-commit     Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-contract  Run contract tests only"
	@echo "  make coverage       Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linter (ruff)"
	@echo "  make format         Format code (black + isort)"
	@echo "  make typecheck      Run type checker (mypy)"
	@echo "  make check          Run all code quality checks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run API in Docker"
	@echo "  make docker-test    Run tests in Docker"
	@echo "  make docker-dev     Run development server in Docker"
	@echo ""
	@echo "Other:"
	@echo "  make clean          Clean up generated files"
	@echo "  make run            Run API server locally"

# Python executable
PYTHON ?= python

# Setup
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

dev: install
	$(PYTHON) -m pip install pytest pytest-cov pytest-asyncio pytest-json-report
	$(PYTHON) -m pip install black isort ruff mypy
	$(PYTHON) -m pip install pre-commit

pre-commit:
	pre-commit install
	pre-commit install --hook-type pre-push

# Testing
test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-unit:
	$(PYTHON) -m pytest tests/unit/ -v --tb=short -m unit

test-integration:
	$(PYTHON) -m pytest tests/integration/ -v --tb=short -m integration

test-contract:
	$(PYTHON) -m pytest tests/contract/ -v --tb=short -m contract

test-fast:
	$(PYTHON) -m pytest tests/unit/ tests/contract/ -v --tb=short -q

coverage:
	$(PYTHON) -m pytest tests/ \
		--cov=core \
		--cov=api \
		--cov=verticals \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--cov-fail-under=70

coverage-html: coverage
	@echo "Opening coverage report..."
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"

# Code Quality
lint:
	$(PYTHON) -m ruff check .

lint-fix:
	$(PYTHON) -m ruff check --fix .

format:
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

format-check:
	$(PYTHON) -m black --check --diff .
	$(PYTHON) -m isort --check-only --diff .

typecheck:
	$(PYTHON) -m mypy core/ api/ --ignore-missing-imports

check: format-check lint typecheck
	@echo "All checks passed!"

# Docker
docker-build:
	docker build -t sovereign-ai:latest .

docker-build-dev:
	docker build --target development -t sovereign-ai:dev .

docker-run:
	docker run -p 8000:8000 --rm sovereign-ai:latest

docker-dev:
	docker-compose --profile dev up api-dev

docker-test:
	docker-compose --profile test run --rm test

docker-down:
	docker-compose down -v

# Local run
run:
	$(PYTHON) -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ coverage.xml .report.json 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true

clean-all: clean
	rm -rf .venv venv 2>/dev/null || true
	docker-compose down -v --rmi local 2>/dev/null || true

# CI simulation (run what CI runs)
ci: format-check lint test-unit test-integration test-contract
	@echo "CI checks passed!"
