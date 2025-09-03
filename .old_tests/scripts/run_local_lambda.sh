#!/bin/bash
# Run Local Lambda Server for Testing
#
# This script starts a local HTTP server that wraps your AWS Lambda handlers
# for testing with ngrok and real Typeform webhooks.

set -e  # Exit on any error

# Change to app directory
cd "$(dirname "$0")/../.."

# Set up environment variables for local testing
export ENVIRONMENT=${ENVIRONMENT:-"local"}
export LOG_LEVEL=${LOG_LEVEL:-"DEBUG"}

# Database configuration (if needed for Lambda handlers)
export DB_HOST=${DB_HOST:-"localhost"}
export DB_PORT=${DB_PORT:-"5432"}
export DB_NAME=${DB_NAME:-"menu_planning_test"}

# Required for client onboarding
if [[ -z "$TYPEFORM_API_KEY" ]]; then
    echo "⚠ Warning: TYPEFORM_API_KEY not set"
fi

if [[ -z "$TYPEFORM_WEBHOOK_SECRET" ]]; then
    echo "⚠ Warning: TYPEFORM_WEBHOOK_SECRET not set"
fi

if [[ -z "$TYPEFORM_TEST_URL" ]]; then
    echo "⚠ Warning: TYPEFORM_TEST_URL not set"
fi

echo "🔧 Environment Setup:"
echo "  Environment: $ENVIRONMENT"
echo "  Log Level: $LOG_LEVEL"
echo ""
echo "📋 Required Environment Variables:"
echo "  TYPEFORM_API_KEY: ${TYPEFORM_API_KEY:+✓ Set}"
echo "  TYPEFORM_WEBHOOK_SECRET: ${TYPEFORM_WEBHOOK_SECRET:+✓ Set}"
echo "  TYPEFORM_TEST_URL: ${TYPEFORM_TEST_URL:+✓ Set}"
echo ""
echo "🚀 Starting Local Lambda Server..."
echo ""

# Run the local server (no external dependencies needed!)
python tests/local_lambda_server.py