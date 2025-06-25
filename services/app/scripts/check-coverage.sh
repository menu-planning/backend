#!/bin/bash
set -e

echo "🧪 Running tests with coverage..."
echo "========================================"

# Run tests with coverage
poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "📊 Coverage threshold validation..."
echo "========================================"

# Extract coverage percentage from the last line
COVERAGE_OUTPUT=$(poetry run pytest --cov=src --cov-report=term-missing --quiet 2>&1 | tail -1)
COVERAGE_PERCENT=$(echo "$COVERAGE_OUTPUT" | grep -oE '[0-9]+%' | sed 's/%//')

if [ -z "$COVERAGE_PERCENT" ]; then
    echo "❌ ERROR: Could not extract coverage percentage"
    exit 1
fi

echo "Current coverage: ${COVERAGE_PERCENT}%"
echo "Required threshold: 90%"

if [ "$COVERAGE_PERCENT" -lt 90 ]; then
    echo "❌ FAILED: Coverage ${COVERAGE_PERCENT}% is below required 90% threshold"
    echo "Please add more tests to increase coverage."
    exit 1
else
    echo "✅ SUCCESS: Coverage ${COVERAGE_PERCENT}% meets the 90% threshold"
fi

echo ""
echo "🎉 All coverage checks passed!" 