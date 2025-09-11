"""
Tests for BaseMiddleware class.

These tests focus on behavior and outcomes rather than implementation details,
ensuring the middleware behaves correctly in various scenarios.
"""

from unittest.mock import AsyncMock

import anyio
import pytest
from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware
from tests.contexts.shared_kernel.middleware.core.no_op_middleware import (
    NoOpMiddleware,
)


class TestBaseMiddleware:
    """Test the BaseMiddleware abstract base class behavior."""

    def test_base_middleware_cannot_be_instantiated(self):
        """Test that BaseMiddleware cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseMiddleware()  # type: ignore[abstract]

    def test_base_middleware_has_name_property(self):
        """Test that middleware has a name property for identification."""
        # Use NoOpMiddleware as a concrete implementation
        middleware = NoOpMiddleware("TestMiddleware")
        assert middleware.name == "TestMiddleware"

    def test_base_middleware_uses_class_name_as_default_name(self):
        """Test that middleware uses class name as default name."""
        middleware = NoOpMiddleware()
        assert middleware.name == "NoOpMiddleware"

    def test_base_middleware_repr_returns_meaningful_string(self):
        """Test that middleware string representation is useful for debugging."""
        middleware = NoOpMiddleware("CustomName")
        expected = "NoOpMiddleware(name='CustomName')"
        assert repr(middleware) == expected


@pytest.mark.anyio
class TestNoOpMiddleware:
    """Test the NoOpMiddleware concrete implementation."""

    async def test_noop_middleware_passes_through_requests_unchanged(self):
        """Test that NoOpMiddleware doesn't modify requests or responses."""
        # Arrange
        middleware = NoOpMiddleware()
        mock_handler = AsyncMock(return_value={"statusCode": 200, "body": "test"})
        test_event = {"httpMethod": "GET", "path": "/test"}

        # Act
        result = await middleware(mock_handler, test_event)

        # Assert
        assert result == {"statusCode": 200, "body": "test"}
        mock_handler.assert_called_once_with(test_event)

    async def test_noop_middleware_preserves_handler_return_value(self):
        """Test that NoOpMiddleware preserves the exact return value from handler."""
        # Arrange
        middleware = NoOpMiddleware()
        expected_response = {"statusCode": 404, "error": "Not Found"}
        mock_handler = AsyncMock(return_value=expected_response)
        test_event = {"httpMethod": "POST", "body": "test data"}

        # Act
        result = await middleware(mock_handler, test_event)

        # Assert
        assert result is expected_response
        assert result["statusCode"] == 404
        assert result["error"] == "Not Found"

    async def test_noop_middleware_handles_different_event_types(self):
        """Test that NoOpMiddleware works with various event structures."""
        # Arrange
        middleware = NoOpMiddleware()
        mock_handler = AsyncMock(return_value={"success": True})

        test_cases = [
            {"httpMethod": "GET", "path": "/simple"},
            {"Records": [{"eventSource": "aws:sqs"}]},
            {"detail": {"eventType": "CustomEvent"}},
            {},  # Empty event
        ]

        # Act & Assert
        for test_event in test_cases:
            result = await middleware(mock_handler, test_event)
            assert result == {"success": True}
            mock_handler.assert_called_with(test_event)

    async def test_noop_middleware_preserves_handler_side_effects(self):
        """Test that NoOpMiddleware doesn't interfere with handler side effects."""
        # Arrange
        middleware = NoOpMiddleware()
        side_effect_called = False

        async def handler_with_side_effect(event):
            nonlocal side_effect_called
            side_effect_called = True
            return {"side_effect_executed": side_effect_called}

        test_event = {"test": "event"}

        # Act
        result = await middleware(handler_with_side_effect, test_event)

        # Assert
        assert side_effect_called is True
        assert result["side_effect_executed"] is True

    async def test_noop_middleware_with_custom_name(self):
        """Test that NoOpMiddleware can be created with a custom name."""
        # Arrange
        custom_name = "PassThroughMiddleware"
        middleware = NoOpMiddleware(custom_name)

        # Assert
        assert middleware.name == custom_name
        assert repr(middleware) == f"NoOpMiddleware(name='{custom_name}')"


@pytest.mark.anyio
class TestMiddlewareIntegration:
    """Test middleware integration patterns and edge cases."""

    async def test_middleware_can_handle_async_handler_exceptions(self):
        """Test that middleware can handle exceptions from async handlers."""
        # Arrange
        middleware = NoOpMiddleware()

        async def failing_handler(event):
            raise ValueError("Handler failed")

        test_event = {"test": "event"}

        # Act & Assert
        with pytest.raises(ValueError, match="Handler failed"):
            await middleware(failing_handler, test_event)

    async def test_middleware_preserves_handler_async_behavior(self):
        """Test that middleware preserves the async nature of handlers."""
        # Arrange
        middleware = NoOpMiddleware()
        execution_order = []

        async def async_handler(event):
            execution_order.append("handler_start")
            await anyio.sleep(0.01)  # Simulate async work
            execution_order.append("handler_end")
            return {"async": "completed"}

        test_event = {"test": "event"}

        # Act
        result = await middleware(async_handler, test_event)

        # Assert
        assert result == {"async": "completed"}
        assert execution_order == ["handler_start", "handler_end"]

    async def test_middleware_with_complex_event_structures(self):
        """Test middleware with complex, nested event structures."""
        # Arrange
        middleware = NoOpMiddleware()
        complex_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123", "email": "test@example.com"}
                }
            },
            "body": {"data": [1, 2, 3], "nested": {"key": "value"}},
            "headers": {"Content-Type": "application/json"},
        }

        mock_handler = AsyncMock(return_value={"processed": True})

        # Act
        result = await middleware(mock_handler, complex_event)

        # Assert
        assert result == {"processed": True}
        mock_handler.assert_called_once_with(complex_event)
