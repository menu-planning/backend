"""
Core middleware components for the unified middleware system.

This package provides the foundational classes and interfaces for building
composable middleware components.
"""

from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware
from src.contexts.shared_kernel.middleware.core.middleware_composer import (
    MiddlewareComposer,
)

__all__ = [
    "BaseMiddleware",
    "MiddlewareComposer",
]
