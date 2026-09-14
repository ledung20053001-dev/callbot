PYTHON ?= python
VENV ?= .venv

.PHONY: help install install-all run test test-ui test-fast test-safety test-integration lint format typecheck check coverage docker-build docker-up docker-down

help:
	@echo "install          Install runtime and development dependencies"
	@echo "install-all      Install all optional integrations"
	@echo "run              Run the development API server"
	@echo "test             Run all tests"
	@echo "test-fast        Run tests that do not require Clinic Mock"
	@echo "test-safety      Run severe-failure guardrail tests"
	@echo "test-integration Run integration tests"
	@echo "check            Run lint, type checks, and tests"
	@echo "docker-up        Build and start the Callbot container"

install:
	$(PYTHON) -m pip install -e ".[dev]"

install-all:
	$(PYTHON) -m pip install -e ".[dev,llm-openai,audio,telephony-twilio]"

run:
	$(PYTHON) -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest

test-ui:
	node --test tests/ui/text-utils.test.mjs

test-fast:
	$(PYTHON) -m pytest -m "not integration and not slow"

test-safety:
	$(PYTHON) -m pytest tests/safety

test-integration:
	$(PYTHON) -m pytest tests/integration

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy src

check: lint typecheck test test-ui

coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing --cov-report=html

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
