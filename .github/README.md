# GitHub Actions Workflows

This directory contains CI/CD workflows for the Mutual Fund Analyser project.

## 📋 Workflows Overview

### 🔄 `ci.yml` - Main CI Pipeline
**Triggers:** Pull Requests to `main`, Direct pushes to `main`

**Jobs:**
1. **🔍 Code Quality & Linting** (3-5 min)
   - Code formatting check with `ruff`
   - Linting with `ruff`
   - Type checking with `mypy`

2. **⚡ Unit Tests** (2-3 min)
   - Fast unit tests without browser dependencies
   - Coverage reporting to Codecov
   - Test result artifacts

3. **🏭 Integration Tests** (10-15 min)
   - Full integration tests with Playwright
   - Browser automation testing
   - Real scraping and analysis pipeline

4. **🧪 Full Test Suite** (15-20 min)
   - Complete test suite with coverage
   - Runs only if all previous jobs pass
   - Comprehensive coverage report

5. **📋 Test Summary**
   - Aggregates results from all jobs
   - Provides clear pass/fail status

### ⚡ `quick-check.yml` - Development Workflow
**Triggers:** Pushes to feature branches (not `main`)

**Purpose:** Fast feedback for developers during development

**Jobs:**
- Combined linting + unit tests (5-8 min)
- No integration tests (for speed)
- Early exit on first failure (`-x` flag)

## 🎯 Workflow Strategy

### **For Feature Development:**
```
Feature Branch Push → Quick Check (⚡ 5-8 min)
├── ✅ Pass: Continue development
└── ❌ Fail: Fix issues before PR
```

### **For Pull Requests:**
```
PR to main → Full CI Pipeline (🔄 25-35 min)
├── 🔍 Linting (parallel)
├── ⚡ Unit Tests (parallel) 
├── 🏭 Integration Tests (parallel)
├── 🧪 Full Suite (after all pass)
└── 📋 Summary
```

### **For Main Branch:**
```
Push to main → Full CI Pipeline + Deployment
```

## 🛠️ CI Environment Setup

### **Dependencies Installation:**
```bash
pip install -e ".[dev]"
```

### **Playwright Setup:**
```bash
playwright install chromium
playwright install-deps chromium
```

### **Environment Variables:**
- `PLAYWRIGHT_BROWSERS_PATH`: Browser cache location
- `PYTHON_VERSION`: Python version (3.12)

## 📊 Coverage & Reporting

- **Coverage Reports:** Uploaded to Codecov
- **Test Results:** JUnit XML format
- **Artifacts:** Test results, coverage reports, failure screenshots

## 🔧 Local Development

To run the same checks locally:

```bash
# Code quality
make format
make lint

# Tests
make test-unit          # Fast unit tests
make test-integration   # Integration tests  
make test              # All tests

# Or manually:
ruff format --check src tests
ruff check src tests
mypy src
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

## 🚀 Performance Optimizations

- **Caching:** pip dependencies and Playwright browsers
- **Parallelization:** Multiple jobs run in parallel
- **Early Exit:** Quick check stops on first failure
- **Concurrency Control:** Cancel in-progress runs for same branch

## 📈 Expected Runtimes

| Workflow | Duration | Use Case |
|----------|----------|----------|
| Quick Check | 5-8 min | Feature development |
| Full CI Pipeline | 25-35 min | PRs and main branch |
| Unit Tests Only | 2-3 min | Fast feedback |
| Integration Tests Only | 10-15 min | Browser testing |

## 🔍 Debugging CI Failures

1. **Linting Failures:** Run `make lint` locally
2. **Unit Test Failures:** Run `make test-unit` locally
3. **Integration Test Failures:** Check Playwright setup, run `make test-integration`
4. **Browser Issues:** Check test artifacts for screenshots
5. **Dependency Issues:** Verify `pyproject.toml` and cache invalidation
