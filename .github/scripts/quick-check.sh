#!/bin/bash
# CI Quick Check Script (for feature branches)
set -e

echo "⚡ Running quick checks (code quality + unit tests)..."

# Run code quality checks
echo "🔍 Code quality checks..."
.github/scripts/check.sh

# Run unit tests with fast exit on failure
echo "⚡ Unit tests (fast mode)..."
.github/scripts/test-unit.sh

echo "🎉 Quick check passed!"
echo "✅ Code formatting: PASSED"
echo "✅ Linting: PASSED"
echo "✅ Type checking: PASSED"
echo "✅ Unit tests: PASSED"
echo ""
echo "💡 Push to main or create PR to run full test suite with integration tests."
