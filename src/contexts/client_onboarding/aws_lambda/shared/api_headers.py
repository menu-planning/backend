"""CORS headers configuration for client onboarding AWS Lambda functions.

Provides standard CORS headers for cross-origin requests from web clients.
"""

CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, Typeform-Signature",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
}

SECURITY_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

API_headers = {**CORS_headers, **SECURITY_headers}
