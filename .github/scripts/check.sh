#!/bin/bash
# CI Code Quality Checks Script
set -e

echo "🔍 Running code quality checks..."

echo "✨ Checking code formatting..."
ruff format --check src tests

echo "🔍 Linting code..."
ruff check src tests

echo "🔎 Type checking..."
mypy src

echo "✅ All code quality checks passed!"
