"""
Authentication middleware module for the shared kernel.

This module provides unified authentication middleware that integrates
with the BaseMiddleware system and follows the established patterns.
"""

from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthContext,
    AuthenticationError,
    AuthenticationMiddleware,
    AuthorizationError,
    AuthPolicy,
    create_auth_middleware,
)

__all__ = [
    "AuthContext",
    "AuthPolicy",
    "AuthenticationError",
    "AuthenticationMiddleware",
    "AuthorizationError",
    "create_auth_middleware",
]
