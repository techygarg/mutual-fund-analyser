#!/bin/bash
# CI Full Test Suite Script
set -e

echo "🧪 Running complete test suite with coverage..."

python -m pytest tests/ \
    --cov=src/mfa \
    --cov-report=xml \
    --cov-report=html \
    --cov-report=term-missing \
    --junitxml=test-results.xml \
    -v

echo "✅ Full test suite completed successfully!"
