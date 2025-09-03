"""
Test fixtures for error handling middleware tests.

This conftest.py file provides shared fixtures for all tests in the
error_handling package, following the test-behavior-focus pattern.
"""

from unittest.mock import AsyncMock

import pytest

from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    ExceptionHandlerMiddleware,
)


@pytest.fixture
def mock_handler():
    """Create a mock handler that can succeed or fail."""
    return AsyncMock()


@pytest.fixture
def mock_event():
    """Create a mock Lambda event."""
    return {"httpMethod": "GET", "path": "/test"}


@pytest.fixture
def error_middleware():
    """Create ExceptionHandlerMiddleware with default settings."""
    return ExceptionHandlerMiddleware(
        name="test_error_handler",
        include_stack_trace=False,
        expose_internal_details=False,
    )


@pytest.fixture
def dev_error_middleware():
    """Create ExceptionHandlerMiddleware with development settings."""
    return ExceptionHandlerMiddleware(
        name="dev_error_handler",
        include_stack_trace=True,
        expose_internal_details=True,
    )
