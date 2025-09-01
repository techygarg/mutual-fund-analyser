# CI Scripts

This directory contains shell scripts for CI/CD operations, keeping the main Makefile clean and focused on development workflows.

## 📋 Scripts Overview

### 🔍 `check.sh` - Code Quality Checks
**Purpose:** Comprehensive code quality validation
**Used by:** `ci.yml` (lint job)
**Commands:**
- `ruff format --check` - Format validation
- `ruff check` - Linting
- `mypy` - Type checking

### ⚡ `test-unit.sh` - Unit Tests
**Purpose:** Fast unit tests with coverage reporting
**Used by:** `ci.yml` (unit-tests job)
**Features:**
- Coverage reporting (XML + terminal)
- JUnit XML output for CI
- Focused on business logic testing

### 🏭 `test-integration.sh` - Integration Tests  
**Purpose:** End-to-end pipeline testing with Playwright
**Used by:** `ci.yml` (integration-tests job)
**Features:**
- Browser automation testing
- Short traceback for CI readability
- JUnit XML output

### 🧪 `test-all.sh` - Complete Test Suite
**Purpose:** Full test coverage analysis
**Used by:** `ci.yml` (full-test-suite job)
**Features:**
- Complete coverage (XML + HTML)
- All test types combined
- Comprehensive reporting

### ⚡ `quick-check.sh` - Development Workflow
**Purpose:** Fast feedback for feature branches
**Used by:** `quick-check.yml`
**Features:**
- Combines code quality + unit tests
- Early exit on failure (-x flag)
- Developer-friendly output

## 🎯 Design Philosophy

### **Separation of Concerns**
- **Makefile:** Development workflow (with venv checks)
- **Shell Scripts:** CI workflow (optimized for GitHub Actions)

### **DRY Principle**
- Single source of truth for CI commands
- No duplication between workflows
- Reusable across different CI providers

### **Maintainability**
- Easy to modify CI behavior without touching workflows
- Clear separation between local dev and CI
- Self-documenting script names

## 🛠️ Local Testing

You can run these scripts locally to test CI behavior:

```bash
# Test code quality (same as CI)
.github/scripts/check.sh

# Test unit tests (same as CI)
.github/scripts/test-unit.sh

# Test integration tests (same as CI)
.github/scripts/test-integration.sh

# Test full suite (same as CI)
.github/scripts/test-all.sh

# Test quick check workflow
.github/scripts/quick-check.sh
```

## 📊 Script Usage Matrix

| Workflow | Script | Purpose | Duration |
|----------|--------|---------|----------|
| `ci.yml` (lint) | `check.sh` | Code quality | 2-3 min |
| `ci.yml` (unit-tests) | `test-unit.sh` | Unit tests | 2-3 min |
| `ci.yml` (integration-tests) | `test-integration.sh` | Integration | 10-15 min |
| `ci.yml` (full-test-suite) | `test-all.sh` | Complete suite | 15-20 min |
| `quick-check.yml` | `quick-check.sh` | Fast feedback | 5-8 min |

## 🔧 Benefits

1. **Clean Makefile** - No CI pollution in development tools
2. **Consistent CI** - Same commands across all workflows  
3. **Easy Maintenance** - Update CI behavior in one place
4. **Local Testing** - Run exact CI commands locally
5. **Provider Agnostic** - Scripts work with any CI provider

## 📝 Adding New Scripts

When adding new CI functionality:

1. Create a new `.sh` script in this directory
2. Make it executable: `chmod +x script-name.sh`
3. Add error handling: `set -e` 
4. Include clear echo messages for CI logs
5. Update this README with usage information
6. Reference from GitHub Actions workflows
