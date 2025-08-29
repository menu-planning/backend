"""
Shared Kernel Middleware

Common middleware components used across all contexts.
"""

# Authentication Middleware
from src.contexts.shared_kernel.middleware.auth_middleware import (
    AuthContext,
    AuthenticationError,
    AuthMiddleware,
    AuthorizationError,
    get_current_user_legacy,
    optional_auth_middleware,
)

# Decorators
from src.contexts.shared_kernel.middleware.decorators import (
    async_endpoint_handler,
    async_endpoint_handler_simple,
)

# Error Middleware
from src.contexts.shared_kernel.middleware.error_middleware import (
    ErrorMiddleware,
)
from src.contexts.shared_kernel.middleware.error_middleware import (
    ErrorType as MiddlewareErrorType,
)

# Logging Middleware
from src.contexts.shared_kernel.middleware.logging_middleware import (
    LoggingMiddleware,
    create_logging_middleware,
)

__all__ = [
    # Authentication
    "AuthContext",
    "AuthMiddleware",
    "optional_auth_middleware",
    "get_current_user_legacy",
    "AuthenticationError",
    "AuthorizationError",
    # Error Handling
    "ErrorMiddleware",
    "MiddlewareErrorType",
    # Logging
    "LoggingMiddleware",
    "create_logging_middleware",
    # Decorators
    "async_endpoint_handler",
    "async_endpoint_handler_simple",
]
