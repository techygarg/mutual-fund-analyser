# MFA - Simple Python Development Makefile

.PHONY: help init install format lint test check clean scrape analyze pipeline orchestrate dashboard status env-check

PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
VENV_ACTIVE := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")

help:
	@echo "MFA - Mutual Fund Analyser"
	@echo "Commands:"
	@echo "  make init        - Setup venv and install dev deps"
	@echo "  make install     - Install deps into active venv"
	@echo "  make format      - Auto-format with ruff"
	@echo "  make lint        - Lint with ruff and mypy"
	@echo "  make test        - Run tests"
	@echo "  make scrape      - Run scraper (URLs via file)"
	@echo "  make analyze     - Analyze collected JSONs"
	@echo "  make pipeline    - Scrape then analyze"
	@echo "  make orchestrate - Run orchestrator (categories from config)"
	@echo "  make dashboard   - Run dashboard server"
	@echo "  make status      - Show environment status"
	@echo "  make env-check   - Check required env vars"

init:
	@if [ -z "$(PYTHON)" ]; then echo "Python not found"; exit 1; fi
	@$(PYTHON) -m venv venv
	@. venv/bin/activate; pip install --upgrade pip; pip install -e ".[dev]"
	@echo "✅ Init complete. Activate: source venv/bin/activate"

install:
	@$(call check_venv)
	@pip install -e ".[dev]"

format:
	@$(call check_venv)
	@ruff format src tests

lint:
	@$(call check_venv)
	@ruff check --fix src tests
	@mypy src

test:
	@$(call check_venv)
	@pytest -q

check: format lint test

clean:
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build src/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

scrape:
	@$(call check_venv)
	@python -m mfa.cli.scrape

analyze:
	@$(call check_venv)
	@python -m mfa.cli.analyze $(if $(DATE),--date $(DATE),) $(if $(CATEGORY),--category $(CATEGORY),)

pipeline:
	@$(call check_venv)
	@python -m mfa.cli.pipeline

orchestrate:
	@$(call check_venv)
	@python -m mfa.cli.orchestrate $(if $(CATEGORY),--category $(CATEGORY),)

dashboard:
	@$(call check_venv)
	@python dashboard/server.py

status:
	@echo "Python: $$(python --version 2>/dev/null || echo 'Not found')"
	@echo "Project: $$(pwd)"
	@echo "Config: $$(test -f config/config.yaml && echo '✅' || echo '❌') config/config.yaml"
	@echo "Env: $$(test -f .env && echo '◦ .env present' || echo '◦ .env missing')"

env-check:
	@$(call check_venv)
	@python -c "import os;print('HTTP_PROXY:', 'set' if os.getenv('HTTP_PROXY') else 'unset');print('HTTPS_PROXY:', 'set' if os.getenv('HTTPS_PROXY') else 'unset')"

define check_venv
	@if [ "$(VENV_ACTIVE)" = "0" ]; then \
		echo "Virtual environment not active"; \
		echo "Run: source venv/bin/activate"; \
		exit 1; \
	fi
endef


