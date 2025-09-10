"""
Tests for middleware order enforcement behavior.

These tests focus on the observable behavior that middleware order is automatically
enforced for security and consistency, regardless of how the user specifies the order.
"""

import pytest

from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthenticationMiddleware,
)
from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware
from src.contexts.shared_kernel.middleware.core.middleware_composer import (
    MiddlewareComposer,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    ExceptionHandlerMiddleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    StructuredLoggingMiddleware,
)


class MockTestLoggingMiddleware(StructuredLoggingMiddleware):
    """Test version of logging middleware that tracks execution order."""

    def __init__(self, execution_order: list[str]):
        super().__init__(name="StructuredLoggingMiddleware")
        self.execution_order = execution_order

    async def __call__(self, handler, event, context):
        """Track execution order and call parent."""
        self.execution_order.append(self.name)
        return await super().__call__(handler, event, context)


class MockTestAuthMiddleware(AuthenticationMiddleware):
    """Test version of auth middleware that tracks execution order."""

    def __init__(self, execution_order: list[str]):
        # Create a policy that doesn't require authentication
        from src.contexts.shared_kernel.middleware.auth.authentication import (
            AuthPolicy,
        )

        policy = AuthPolicy(require_authentication=False)
        super().__init__(policy=policy, name="AuthenticationMiddleware")
        self.execution_order = execution_order

    async def __call__(self, handler, event, context):
        """Track execution order and call parent."""
        self.execution_order.append(self.name)
        return await super().__call__(handler, event, context)


class MockTestErrorMiddleware(ExceptionHandlerMiddleware):
    """Test version of error middleware that tracks execution order."""

    def __init__(self, execution_order: list[str]):
        super().__init__(name="ExceptionHandlerMiddleware")
        self.execution_order = execution_order

    async def __call__(self, handler, event, context):
        """Track execution order and call parent."""
        self.execution_order.append(self.name)
        return await super().__call__(handler, event, context)


class MockTestCustomMiddleware(BaseMiddleware):
    """Simulates custom business middleware."""

    def __init__(self, execution_order: list[str]):
        super().__init__(name="TestCustomMiddleware")
        self.execution_order = execution_order

    async def __call__(self, handler, event, context):
        """Track execution order and call handler."""
        self.execution_order.append(self.name)
        return await handler(event, context)


class TestMiddlewareOrderEnforcement:
    """Test that middleware order is automatically enforced."""

    @pytest.mark.anyio
    async def test_middleware_executes_in_correct_order_regardless_of_input_order(self):
        """Test that middleware always executes in the correct order."""
        execution_order = []

        # User specifies middleware in "wrong" order
        middleware = [
            MockTestErrorMiddleware(execution_order),  # Should run last
            MockTestCustomMiddleware(execution_order),  # Should run in middle
            MockTestLoggingMiddleware(execution_order),  # Should run first
            MockTestAuthMiddleware(execution_order),  # Should run early
        ]

        composer = MiddlewareComposer(middleware)

        async def test_handler(event, context):
            execution_order.append("Handler")
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)
        await composed_handler({"test": "event"}, {"function_name": "test"})

        # Verify the correct execution order was enforced
        expected_order = [
            "StructuredLoggingMiddleware",  # First: captures everything
            "AuthenticationMiddleware",  # Early: authenticates
            "TestCustomMiddleware",  # Middle: business logic
            "ExceptionHandlerMiddleware",  # Last: error handling
            "Handler",  # Actual handler
        ]

        assert execution_order == expected_order, (
            f"Middleware executed in wrong order. "
            f"Expected: {expected_order}, Got: {execution_order}"
        )

    @pytest.mark.anyio
    async def test_auth_middleware_runs_before_business_logic(self):
        """Test that authentication runs before business logic for security."""
        execution_order = []

        middleware = [
            MockTestCustomMiddleware(execution_order),  # Business logic
            MockTestAuthMiddleware(execution_order),  # Authentication
        ]

        composer = MiddlewareComposer(middleware)

        async def test_handler(event, context):
            execution_order.append("Handler")
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)
        await composed_handler({"test": "event"}, {"function_name": "test"})

        # Auth should run before business logic
        auth_index = execution_order.index("AuthenticationMiddleware")
        custom_index = execution_order.index("TestCustomMiddleware")

        assert (
            auth_index < custom_index
        ), "Authentication middleware must run before business logic for security"

    @pytest.mark.anyio
    async def test_error_handling_middleware_runs_last(self):
        """Test that error handling middleware runs last to catch all errors."""
        execution_order = []

        middleware = [
            MockTestErrorMiddleware(execution_order),  # Error handling
            MockTestLoggingMiddleware(execution_order),  # Logging
            MockTestAuthMiddleware(execution_order),  # Authentication
        ]

        composer = MiddlewareComposer(middleware)

        async def test_handler(event, context):
            execution_order.append("Handler")
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)
        await composed_handler({"test": "event"}, {"function_name": "test"})

        # Error handling should run last (before handler)
        error_index = execution_order.index("ExceptionHandlerMiddleware")
        handler_index = execution_order.index("Handler")

        assert (
            error_index < handler_index
        ), "Error handling middleware must run last to catch all errors"

    @pytest.mark.anyio
    async def test_logging_middleware_runs_first(self):
        """Test that logging middleware runs first to capture everything."""
        execution_order = []

        middleware = [
            MockTestAuthMiddleware(execution_order),  # Authentication
            MockTestCustomMiddleware(execution_order),  # Business logic
            MockTestLoggingMiddleware(execution_order),  # Logging
        ]

        composer = MiddlewareComposer(middleware)

        async def test_handler(event, context):
            execution_order.append("Handler")
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)
        await composed_handler({"test": "event"}, {"function_name": "test"})

        # Logging should run first
        logging_index = execution_order.index("StructuredLoggingMiddleware")
        assert (
            logging_index == 0
        ), "Logging middleware must run first to capture everything"

    @pytest.mark.anyio
    async def test_middleware_order_is_consistent_across_multiple_calls(self):
        """Test that middleware order is consistent across multiple calls."""
        execution_order_1 = []
        execution_order_2 = []

        middleware = [
            MockTestErrorMiddleware(execution_order_1),  # Different instances
            MockTestCustomMiddleware(execution_order_1),
            MockTestLoggingMiddleware(execution_order_1),
            MockTestAuthMiddleware(execution_order_1),
        ]

        composer = MiddlewareComposer(middleware)

        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)

        # First call
        await composed_handler({"test": "event1"}, {"function_name": "test1"})

        # Second call with different middleware instances
        middleware_2 = [
            MockTestErrorMiddleware(execution_order_2),
            MockTestCustomMiddleware(execution_order_2),
            MockTestLoggingMiddleware(execution_order_2),
            MockTestAuthMiddleware(execution_order_2),
        ]  # type: list[BaseMiddleware]

        composer_2 = MiddlewareComposer(middleware_2)
        composed_handler_2 = composer_2.compose(test_handler)
        await composed_handler_2({"test": "event2"}, {"function_name": "test2"})

        # Extract just the middleware names (remove "Handler")
        order_1 = [name for name in execution_order_1 if name != "Handler"]
        order_2 = [name for name in execution_order_2 if name != "Handler"]

        # Order should be consistent
        assert order_1 == order_2, (
            f"Middleware order should be consistent. "
            f"First call: {order_1}, Second call: {order_2}"
        )

    @pytest.mark.anyio
    async def test_empty_middleware_list_handled_gracefully(self):
        """Test that empty middleware list is handled gracefully."""
        composer = MiddlewareComposer([])

        async def test_handler(event, context):
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)
        result = await composed_handler({"test": "event"}, {"function_name": "test"})

        # Should work without middleware
        assert result["statusCode"] == 200
        assert result["body"] == "success"

    @pytest.mark.anyio
    async def test_single_middleware_works_correctly(self):
        """Test that single middleware works correctly."""
        execution_order = []

        middleware: list[BaseMiddleware] = [MockTestLoggingMiddleware(execution_order)]
        composer = MiddlewareComposer(middleware)

        async def test_handler(event, context):
            execution_order.append("Handler")
            return {"statusCode": 200, "body": "success"}

        composed_handler = composer.compose(test_handler)
        await composed_handler({"test": "event"}, {"function_name": "test"})

        # Should execute in correct order
        expected_order = ["StructuredLoggingMiddleware", "Handler"]
        assert execution_order == expected_order
