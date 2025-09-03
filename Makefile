# MFA - Mutual Fund Analyser - Streamlined Makefile

.PHONY: help init format lint check clean test test-unit test-integration analyze dashboard status verify-build

# ==============================================================================
# CONFIGURATION
# ==============================================================================
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
VENV_ACTIVE := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")

# Colors for better output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# ==============================================================================
# HELP & SETUP COMMANDS
# ==============================================================================

help:
	@echo "$(BLUE)🚀 MFA - Mutual Fund Analyser$(NC)"
	@echo ""
	@echo "$(GREEN)📦 Setup Commands:$(NC)"
	@echo "  make init        - 🏗️  Setup venv and install dev deps (recommended for new users)"
	@echo ""
	@echo "$(GREEN)🔧 Development Commands:$(NC)"
	@echo "  make format      - ✨ Auto-format code with ruff"
	@echo "  make lint        - 🔍 Lint with ruff and mypy"
	@echo "  make check       - ✅ Run format + lint"
	@echo "  make clean       - 🧹 Clean build artifacts and cache"
	@echo "  make test        - 🧪 Run all tests (unit + integration)"
	@echo "  make test-unit   - ⚡ Run unit tests only (fast)"
	@echo "  make test-integration - 🏭 Run integration tests only"
	@echo "  make verify-build - 🏗️ Verify build integrity"
	@echo "  make status      - 📋 Show project status and health"
	@echo ""
	@echo "$(GREEN)🏃‍♂️ Application Commands:$(NC)"
	@echo "  make analyze     - 📊 Extract and analyze fund data (scrape + analyze)"
	@echo "  make dashboard   - 🌐 Run dashboard server"
	@echo ""
	@echo "$(YELLOW)💡 Quick Start: make init && source venv/bin/activate$(NC)"

# ==============================================================================
# SETUP COMMANDS
# ==============================================================================

init:
	@echo "$(BLUE)🏗️ Initializing virtual environment...$(NC)"
	@if [ -z "$(PYTHON)" ]; then echo "$(RED)❌ Python not found$(NC)"; exit 1; fi
	@if [ -d "venv" ]; then echo "$(YELLOW)⚠️  venv already exists, skipping creation$(NC)"; else $(PYTHON) -m venv venv; fi
	@. venv/bin/activate; pip install --upgrade pip; pip install -e ".[dev]"
	@echo "$(GREEN)✅ Virtual environment ready$(NC)"
	@echo "$(YELLOW)💡 Activate with: source venv/bin/activate$(NC)"

# ==============================================================================
# DEVELOPMENT COMMANDS
# ==============================================================================

format:
	@$(call check_venv)
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@ruff format src tests
	@echo "$(GREEN)✅ Code formatted$(NC)"

lint:
	@$(call check_venv)
	@echo "$(BLUE)🔍 Linting code...$(NC)"
	@ruff check --fix src
	@mypy src
	@echo "$(GREEN)✅ Linting complete$(NC)"



clean:
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	@rm -rf .mypy_cache .ruff_cache dist build src/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

test:
	@$(call check_venv)
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	@python -m pytest tests/ -v
	@echo "$(GREEN)✅ All tests complete$(NC)"

test-unit:
	@$(call check_venv)
	@echo "$(BLUE)🏭 Running unit tests...$(NC)"
	@python -m pytest tests/unit/ -v
	@echo "$(GREEN)✅ Unit tests complete$(NC)"

test-integration:
	@$(call check_venv)
	@echo "$(BLUE)🏭 Running integration tests...$(NC)"
	@python -m pytest tests/integration/ -v
	@echo "$(GREEN)✅ Integration tests complete$(NC)"

# ==============================================================================
# APPLICATION COMMANDS
# ==============================================================================

analyze:
	@$(call check_venv)
	@echo "$(BLUE)📊 Running Mutual Fund Analysis...$(NC)"
	@echo "$(BLUE)   This will extract fund data and perform analysis$(NC)"
	@mfa-analyze $(if $(DATE),--date $(DATE),) $(if $(CATEGORY),--category $(CATEGORY),) $(if $(VERBOSE),--verbose,) || (echo "$(RED)❌ Analysis failed. Check logs for details.$(NC)" && exit 1)

dashboard:
	@$(call check_venv)
	@echo "$(BLUE)🌐 Starting dashboard...$(NC)"
	@python -m mfa.web.server

# ==============================================================================
# STATUS & VALIDATION
# ==============================================================================

status:
	@echo "$(BLUE)📋 MFA Project Status$(NC)"
	@echo ""
	@echo "$(YELLOW)🐍 Environment:$(NC)"
	@echo "  Python: $$(python --version 2>/dev/null || echo '$(RED)❌ Not found$(NC)')"
	@echo "  Virtual Environment: $(if $(filter 1,$(VENV_ACTIVE)),$(GREEN)✅ Active$(NC),$(RED)❌ Not active$(NC))"
	@echo "  Working Directory: $$(pwd)"
	@echo ""
	@echo "$(YELLOW)📁 Project Files:$(NC)"
	@echo "  Config: $$(test -f config/config.yaml && echo '$(GREEN)✅$(NC)' || echo '$(RED)❌$(NC)') config/config.yaml"
	@echo "  Package: $$(python -c 'import mfa' 2>/dev/null && echo '$(GREEN)✅ Installed$(NC)' || echo '$(RED)❌ Not installed$(NC)')"
	@echo "  Playwright: $$(playwright --version >/dev/null 2>&1 && echo '$(GREEN)✅ Available$(NC)' || echo '$(YELLOW)⚠️ Run: playwright install$(NC)')"

# ==============================================================================
# VERIFICATION & VALIDATION
# ==============================================================================
verify-build:
	@echo "$(BLUE)🏗️ Verifying build integrity...$(NC)"
	@python -c "import mfa; print(f'✅ Package version: {mfa.__version__ if hasattr(mfa, \"__version__\") else \"OK\"}')"
	@python -m pip check 2>/dev/null || echo "$(YELLOW)⚠️  Some dependencies may have conflicts$(NC)"
	@python scripts/verify-build.py
	@echo "$(GREEN)✅ Build verification complete!$(NC)"

check: verify-build format lint test-unit
	@echo "$(GREEN)✅ All checks passed!$(NC)"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

define check_venv
	@if [ "$(VENV_ACTIVE)" = "0" ]; then \
		echo "$(RED)❌ Virtual environment not active$(NC)"; \
		echo "$(YELLOW)💡 Run: source venv/bin/activate$(NC)"; \
		exit 1; \
	fi
endef
