"""
Decorators module for the unified middleware system.

This module provides decorators that simplify the use of middleware
composition in AWS Lambda functions and other async handlers.
"""

from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
    async_endpoint_handler_simple,
)

__all__ = ["async_endpoint_handler", "async_endpoint_handler_simple"]
