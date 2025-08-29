"""
Logging middleware package for the unified middleware system.

This package provides structured logging middleware that integrates with the
existing correlation ID system and provides consistent logging across all endpoints.
"""

from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    StructuredLoggingMiddleware,
)

__all__ = ["StructuredLoggingMiddleware"]
