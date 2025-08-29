"""
Middleware adapters for client_onboarding context.

This package contains middleware components that provide cross-cutting concerns
for the client onboarding context, including authentication, authorization,
and request processing.
"""

from src.contexts.client_onboarding.core.adapters.middleware.auth_middleware import (
    create_client_onboarding_auth_middleware,
)
from src.contexts.client_onboarding.core.adapters.middleware.error_middleware import (
    create_client_onboarding_error_middleware,
)
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_api_logging_middleware,
    create_development_logging_middleware,
    create_webhook_logging_middleware,
)

__all__ = [
    "create_api_logging_middleware",
    "create_client_onboarding_auth_middleware",
    "create_client_onboarding_error_middleware",
    "create_development_logging_middleware",
    "create_webhook_logging_middleware",
]
