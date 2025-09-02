"""Default CORS headers for IAM Lambda responses.

Provides standard CORS headers for cross-origin requests to IAM endpoints.
Allows all origins with common headers and methods for IAM operations.
"""

CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}
