#!/bin/bash
# CI Integration Tests Script
set -e

echo "🏭 Running integration tests..."

python -m pytest tests/integration/ \
    --junitxml=integration-test-results.xml \
    --tb=short \
    -v

echo "✅ Integration tests completed successfully!"
