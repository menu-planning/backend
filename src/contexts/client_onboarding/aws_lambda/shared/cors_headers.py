"""CORS headers configuration for client onboarding AWS Lambda functions.

Provides standard CORS headers for cross-origin requests from web clients.
"""

CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, Typeform-Signature",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
}
