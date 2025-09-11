"""
Tests for MiddlewareComposer class.

These tests focus on behavior and outcomes rather than implementation details,
ensuring the middleware composition works correctly in various scenarios.
"""

import pytest

from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware
from src.contexts.shared_kernel.middleware.core.middleware_composer import (
    MiddlewareComposer,
)


class MockMiddleware(BaseMiddleware):
    """Mock middleware for testing composition behavior."""

    def __init__(self, name: str, execution_order: list):
        super().__init__(name)
        self.execution_order = execution_order

    async def __call__(self, handler, event, context):
        self.execution_order.append(f"{self.name}_pre")
        result = await handler(event, context)
        self.execution_order.append(f"{self.name}_post")
        return result


class TestMiddlewareComposer:
    """Test the MiddlewareComposer behavior."""

    def test_composer_initialization_with_middleware_list(self):
        """Test that composer can be initialized with a list of middleware."""
        # Arrange
        middleware1 = MockMiddleware("First", [])
        middleware2 = MockMiddleware("Second", [])

        # Act
        composer = MiddlewareComposer([middleware1, middleware2])

        # Assert
        assert len(composer) == 2
        assert list(composer.middleware) == [middleware1, middleware2]

    def test_composer_initialization_with_empty_list(self):
        """Test that composer can be initialized with an empty middleware list."""
        # Arrange & Act
        composer = MiddlewareComposer([])

        # Assert
        assert len(composer) == 0
        assert list(composer.middleware) == []

    def test_composer_length_returns_correct_count(self):
        """Test that composer length reflects the number of middleware components."""
        # Arrange
        middleware_list = [
            MockMiddleware("One", []),
            MockMiddleware("Two", []),
            MockMiddleware("Three", []),
        ]
        composer = MiddlewareComposer(middleware_list)

        # Act & Assert
        assert len(composer) == 3

    def test_composer_repr_returns_meaningful_string(self):
        """Test that composer string representation is useful for debugging."""
        # Arrange
        middleware1 = MockMiddleware("Auth", [])
        middleware2 = MockMiddleware("Logging", [])
        composer = MiddlewareComposer([middleware1, middleware2])

        # Act
        result = repr(composer)

        # Assert
        assert "MiddlewareComposer" in result
        assert "Auth" in result
        assert "Logging" in result


@pytest.mark.anyio
class TestMiddlewareComposition:
    """Test middleware composition behavior and execution order."""

    async def test_composer_with_single_middleware(self):
        """Test composition with a single middleware component."""
        # Arrange
        execution_order = []
        middleware = MockMiddleware("Single", execution_order)
        composer = MiddlewareComposer([middleware])

        async def test_handler(event, context):
            execution_order.append("handler")
            return {"status": "success"}

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act
        composed_handler = composer.compose(test_handler)
        result = await composed_handler(test_event, test_context)

        # Assert
        assert result == {"status": "success"}
        assert execution_order == ["Single_pre", "handler", "Single_post"]

    async def test_composer_with_multiple_middleware_execution_order(self):
        """Test that middleware executes in the correct order (outermost first)."""
        # Arrange
        execution_order = []
        middleware1 = MockMiddleware("First", execution_order)
        middleware2 = MockMiddleware("Second", execution_order)
        middleware3 = MockMiddleware("Third", execution_order)

        composer = MiddlewareComposer([middleware1, middleware2, middleware3])

        async def test_handler(event, context):
            execution_order.append("handler")
            return {"status": "success"}

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act
        composed_handler = composer.compose(test_handler)
        result = await composed_handler(test_event, test_context)

        # Assert
        assert result == {"status": "success"}
        expected_order = [
            "First_pre",
            "Second_pre",
            "Third_pre",
            "handler",
            "Third_post",
            "Second_post",
            "First_post",
        ]
        assert execution_order == expected_order

    async def test_composer_preserves_handler_return_value(self):
        """Test that composed middleware preserves the handler's return value."""
        # Arrange
        execution_order = []
        middleware = MockMiddleware("Preserve", execution_order)
        composer = MiddlewareComposer([middleware])

        expected_response = {"statusCode": 200, "body": "Hello World"}

        async def test_handler(event, context):
            execution_order.append("handler")
            return expected_response

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act
        composed_handler = composer.compose(test_handler)
        result = await composed_handler(test_event, test_context)

        # Assert
        assert result is expected_response
        assert result["statusCode"] == 200
        assert result["body"] == "Hello World"

    async def test_composer_with_no_middleware_passes_through(self):
        """Test that composer with no middleware passes through to handler directly."""
        # Arrange
        composer = MiddlewareComposer([])

        async def test_handler(event, context):
            return {"direct": "call"}

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act
        composed_handler = composer.compose(test_handler)
        result = await composed_handler(test_event, test_context)

        # Assert
        assert result == {"direct": "call"}

    async def test_composer_preserves_event_data(self):
        """Test that composed middleware doesn't modify the event data."""
        # Arrange
        execution_order = []
        middleware = MockMiddleware("DataPreserve", execution_order)
        composer = MiddlewareComposer([middleware])

        original_event = {
            "httpMethod": "POST",
            "body": "test data",
            "headers": {"Content-Type": "application/json"},
        }

        async def test_handler(event, context):
            execution_order.append("handler")
            # Verify event is unchanged
            assert event == original_event
            return {"received": event}

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act
        composed_handler = composer.compose(test_handler)
        result = await composed_handler(original_event, test_context)

        # Assert
        assert result["received"] == original_event


class TestMiddlewareComposerModifications:
    """Test middleware composer modification methods."""

    def test_add_middleware_append(self):
        """Test adding middleware to the end of the composition."""
        # Arrange
        composer = MiddlewareComposer([])
        middleware1 = MockMiddleware("First", [])
        middleware2 = MockMiddleware("Second", [])

        # Act
        composer.add_middleware(middleware1)
        composer.add_middleware(middleware2)

        # Assert
        assert len(composer) == 2
        assert composer.middleware == [middleware1, middleware2]

    def test_add_middleware_at_position(self):
        """Test adding middleware at a specific position."""
        # Arrange
        middleware1 = MockMiddleware("First", [])
        middleware2 = MockMiddleware("Second", [])
        composer = MiddlewareComposer([middleware1])

        # Act
        composer.add_middleware(middleware2, position=0)

        # Assert
        assert len(composer) == 2
        assert composer.middleware == [middleware2, middleware1]

    def test_remove_middleware(self):
        """Test removing middleware from the composition."""
        # Arrange
        middleware1 = MockMiddleware("First", [])
        middleware2 = MockMiddleware("Second", [])
        composer = MiddlewareComposer([middleware1, middleware2])

        # Act
        composer.remove_middleware(middleware1)

        # Assert
        assert len(composer) == 1
        assert composer.middleware == [middleware2]

    def test_remove_nonexistent_middleware(self):
        """Test removing middleware that doesn't exist in the composition."""
        # Arrange
        middleware1 = MockMiddleware("First", [])
        middleware2 = MockMiddleware("Second", [])
        composer = MiddlewareComposer([middleware1])

        # Act
        composer.remove_middleware(middleware2)  # Not in composition

        # Assert
        assert len(composer) == 1
        assert composer.middleware == [middleware1]

    def test_clear_middleware(self):
        """Test clearing all middleware from the composition."""
        # Arrange
        middleware1 = MockMiddleware("First", [])
        middleware2 = MockMiddleware("Second", [])
        composer = MiddlewareComposer([middleware1, middleware2])

        # Act
        composer.clear()

        # Assert
        assert len(composer) == 0
        assert composer.middleware == []


class TestMiddlewareComposerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.anyio
    async def test_composer_with_middleware_that_modifies_response(self):
        """Test composition with middleware that modifies the response."""
        # Arrange
        execution_order = []

        class ResponseModifyingMiddleware(BaseMiddleware):
            def __init__(self, name: str, execution_order: list):
                super().__init__(name)
                self.execution_order = execution_order

            async def __call__(self, handler, event, context):
                self.execution_order.append(f"{self.name}_pre")
                result = await handler(event, context)
                self.execution_order.append(f"{self.name}_post")
                # Modify the response
                if isinstance(result, dict):
                    result["modified_by"] = self.name
                return result

        middleware = ResponseModifyingMiddleware("Modifier", execution_order)
        composer = MiddlewareComposer([middleware])

        async def test_handler(event, context):
            execution_order.append("handler")
            return {"original": "response"}

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act
        composed_handler = composer.compose(test_handler)
        result = await composed_handler(test_event, test_context)

        # Assert
        assert result["original"] == "response"
        assert result["modified_by"] == "Modifier"
        assert execution_order == ["Modifier_pre", "handler", "Modifier_post"]

    @pytest.mark.anyio
    async def test_composer_with_middleware_that_raises_exception(self):
        """Test composition with middleware that raises an exception."""

        # Arrange
        class ExceptionMiddleware(BaseMiddleware):
            def __init__(self, name: str):
                super().__init__(name)

            async def __call__(self, handler, event, context):
                raise ValueError("Test exception")

        middleware = ExceptionMiddleware("Failing")
        composer = MiddlewareComposer([middleware])

        async def test_handler(event, context):
            return {"should": "not reach"}

        test_event = {"test": "event"}
        test_context = {"function_name": "test"}

        # Act & Assert
        composed_handler = composer.compose(test_handler)
        with pytest.raises(ValueError, match="Test exception"):
            await composed_handler(test_event, test_context)

    def test_composer_repr_with_empty_middleware(self):
        """Test composer string representation with empty middleware list."""
        # Arrange
        composer = MiddlewareComposer([])

        # Act
        result = repr(composer)

        # Assert
        assert result == "MiddlewareComposer(middleware=[])"
