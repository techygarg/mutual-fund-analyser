#!/bin/bash
# CI Unit Tests Script
set -e

echo "⚡ Running unit tests with coverage..."

python -m pytest tests/unit/ \
    --cov=src/mfa \
    --cov-report=xml \
    --cov-report=term-missing \
    --junitxml=unit-test-results.xml \
    -v

echo "✅ Unit tests completed successfully!"
