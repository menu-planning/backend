"""Default CORS headers for Products Catalog Lambda responses.

This module provides standardized CORS headers for all AWS Lambda endpoints
in the products catalog context. The headers enable cross-origin requests
from web applications while maintaining security boundaries.

Notes:
    - Allows all origins (*) for development; should be restricted in production
    - Supports Authorization and Content-Type headers for API authentication
    - Permits GET, POST, and OPTIONS methods for RESTful operations
    - Used by all Lambda handlers in this context for consistent CORS behavior
"""

CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
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
