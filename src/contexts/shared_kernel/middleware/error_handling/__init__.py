"""
Error handling middleware package for the unified middleware system.

This package provides consistent error handling and exception management
across all Lambda functions and API endpoints.
"""

from .exception_handler import ExceptionHandlerMiddleware

__all__ = ["ExceptionHandlerMiddleware"]
