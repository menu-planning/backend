"""
Tests for the lambda handler decorator.

This module tests the lambda_handler decorator functionality, including
middleware composition, timeout handling, and metadata preservation.
"""

import pytest

from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware
from src.contexts.shared_kernel.middleware.decorators import (
    async_endpoint_handler_simple,
    lambda_handler,
)


class MockMiddleware(BaseMiddleware):
    """Mock middleware for testing."""

    def __init__(self, name: str = "MockMiddleware", should_fail: bool = False):
        super().__init__(name=name)
        self.should_fail = should_fail
        self.called = False
        self.pre_called = False
        self.post_called = False

    async def __call__(self, handler, event, context):
        """Execute mock middleware."""
        self.called = True
        self.pre_called = True

        try:
            result = await handler(event, context)
            self.post_called = True
            return result
        except Exception as e:
            self.post_called = True
            if self.should_fail:
                # Re-raise the exception to test error propagation
                raise e
            # If not failing, we need to handle the case where result wasn't set
            # This simulates middleware that catches and handles errors
            return {"statusCode": 500, "body": "Error handled by middleware"}


class TestLambdaHandlerDecorator:
    """Test cases for the lambda_handler decorator."""

    @pytest.mark.anyio
    async def test_basic_decorator_functionality(self):
        """Test basic decorator functionality with single middleware."""
        middleware = MockMiddleware("TestMiddleware")

        @lambda_handler(middleware)
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Verify middleware was applied
        assert hasattr(test_handler, "_middleware_info")
        assert test_handler._middleware_info["middleware_count"] == 1
        assert test_handler._middleware_info["middleware_names"] == ["TestMiddleware"]

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200
        assert result["body"] == "success"
        assert middleware.called
        assert middleware.pre_called
        assert middleware.post_called

    @pytest.mark.anyio
    async def test_multiple_middleware_composition(self):
        """Test decorator with multiple middleware components."""
        middleware1 = MockMiddleware("FirstMiddleware")
        middleware2 = MockMiddleware("SecondMiddleware")

        @lambda_handler(middleware1, middleware2)
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Verify middleware composition
        assert test_handler._middleware_info["middleware_count"] == 2
        assert "FirstMiddleware" in test_handler._middleware_info["middleware_names"]
        assert "SecondMiddleware" in test_handler._middleware_info["middleware_names"]

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200
        assert middleware1.called
        assert middleware2.called

    @pytest.mark.anyio
    async def test_timeout_configuration(self):
        """Test decorator with timeout configuration."""
        middleware = MockMiddleware("TimeoutMiddleware")

        @lambda_handler(middleware, timeout=5.0)
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Verify timeout configuration
        assert test_handler._middleware_info["timeout"] == 5.0

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200

    @pytest.mark.anyio
    async def test_custom_name_configuration(self):
        """Test decorator with custom name configuration."""
        middleware = MockMiddleware("NamedMiddleware")

        @lambda_handler(middleware, name="CustomHandlerName")
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Verify custom name
        assert test_handler._middleware_info["decorator_name"] == "CustomHandlerName"

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200

    @pytest.mark.anyio
    async def test_no_middleware_decorator(self):
        """Test decorator with no middleware (edge case)."""

        @lambda_handler()
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Verify no middleware configuration
        assert test_handler._middleware_info["middleware_count"] == 0
        assert test_handler._middleware_info["middleware_names"] == []

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200

    @pytest.mark.anyio
    async def test_function_metadata_preservation(self):
        """Test that function metadata is preserved by the decorator."""

        @lambda_handler()
        async def test_handler(event, context):
            """Test handler with docstring."""
            return {"statusCode": 200, "body": "success"}

        # Verify metadata preservation
        assert test_handler.__name__ == "test_handler"
        assert test_handler.__doc__ == "Test handler with docstring."
        # Note: __module__ might be different in test environment
        assert "test_lambda_handler" in test_handler.__module__

    @pytest.mark.anyio
    async def test_middleware_error_handling(self):
        """Test decorator behavior when handler raises exceptions."""
        middleware = MockMiddleware("ErrorHandlingMiddleware", should_fail=False)

        @lambda_handler(middleware)
        async def test_handler(event, context):
            if event.get("should_fail"):
                raise ValueError("Handler error for testing")
            return {"statusCode": 200, "body": "success"}

        # Test successful execution
        result = await test_handler({"should_fail": False}, {"function_name": "test"})
        assert result["statusCode"] == 200
        assert result["body"] == "success"

        # Test error handling - middleware should catch and handle the error
        result = await test_handler({"should_fail": True}, {"function_name": "test"})
        assert result["statusCode"] == 500
        assert result["body"] == "Error handled by middleware"

        # Test that middleware was called in both cases
        assert middleware.called
        assert middleware.pre_called
        assert middleware.post_called


class TestLambdaHandlerSimpleDecorator:
    """Test cases for the lambda_handler_simple decorator."""

    @pytest.mark.anyio
    async def test_simple_decorator_functionality(self):
        """Test simple decorator functionality."""
        middleware = MockMiddleware("SimpleMiddleware")

        @async_endpoint_handler_simple(middleware)
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Verify no metadata (simple version)
        assert not hasattr(test_handler, "_middleware_info")

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200
        assert result["body"] == "success"
        assert middleware.called

    @pytest.mark.anyio
    async def test_simple_decorator_multiple_middleware(self):
        """Test simple decorator with multiple middleware."""
        middleware1 = MockMiddleware("FirstSimpleMiddleware")
        middleware2 = MockMiddleware("SecondSimpleMiddleware")

        @async_endpoint_handler_simple(middleware1, middleware2)
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200
        assert middleware1.called
        assert middleware2.called

    @pytest.mark.anyio
    async def test_simple_decorator_timeout(self):
        """Test simple decorator with timeout."""
        middleware = MockMiddleware("TimeoutSimpleMiddleware")

        @async_endpoint_handler_simple(middleware, timeout=10.0)
        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        # Test execution
        result = await test_handler({"test": "event"}, {"function_name": "test"})
        assert result["statusCode"] == 200
        assert middleware.called


class TestDecoratorIntegration:
    """Integration tests for decorator with real middleware patterns."""

    @pytest.mark.anyio
    async def test_decorator_with_real_middleware_types(self):
        """Test decorator with actual middleware types (if available)."""
        # This test would use actual middleware implementations
        # For now, we'll test with our mock middleware
        middleware = MockMiddleware("IntegrationMiddleware")

        @lambda_handler(middleware, timeout=30.0, name="IntegrationTest")
        async def integration_handler(event, context):
            # Simulate some business logic
            if event.get("should_fail"):
                raise ValueError("Business logic failure")
            return {"statusCode": 200, "body": "integration_success"}

        # Test successful execution
        result = await integration_handler(
            {"should_fail": False}, {"function_name": "test"}
        )
        assert result["statusCode"] == 200
        assert result["body"] == "integration_success"

        # Test error handling - middleware should catch and handle the error
        result = await integration_handler(
            {"should_fail": True}, {"function_name": "test"}
        )
        assert result["statusCode"] == 500
        assert result["body"] == "Error handled by middleware"
