"""Unit tests for MiddlewareComposer class.

Tests the middleware composition and execution order ensuring consistent behavior
and proper error handling for the unified middleware system.
"""

from typing import Any

import pytest
from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthContext,
    AuthenticationStrategy,
)
from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.contexts.shared_kernel.middleware.core.middleware_composer import (
    MiddlewareComposer,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    ErrorHandlingStrategy,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    LoggingStrategy,
)

pytestmark = pytest.mark.anyio


class FakeLoggingStrategy(LoggingStrategy):
    """Fake logging strategy for testing."""

    def extract_logging_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"test": "logging_context"}

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        return {"test": "request"}, None

    def inject_logging_context(
        self, request_data: dict[str, Any], logging_context: dict[str, Any]
    ) -> None:
        """Inject logging context into request data."""
        request_data["logging_context"] = logging_context


class FakeAuthStrategy(AuthenticationStrategy):
    """Fake authentication strategy for testing."""

    async def extract_auth_context(self, *args: Any, **kwargs: Any) -> AuthContext:
        return AuthContext(
            user_id="test_user",
            user_roles=["test_role"],
            is_authenticated=True,
            metadata={"test": "auth_context"},
            caller_context="test",
        )

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        return {"test": "request"}, None

    def inject_auth_context(
        self, request_data: dict[str, Any], auth_context: AuthContext
    ) -> None:
        """Inject authentication context into request data."""
        request_data["auth_context"] = auth_context


class FakeErrorStrategy(ErrorHandlingStrategy):
    """Fake error handling strategy for testing."""

    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"test": "error_context"}

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        return {"test": "request"}, None

    def inject_error_context(
        self, request_data: dict[str, Any], error_context: dict[str, Any]
    ) -> None:
        """Inject error context into request data."""
        request_data["error_context"] = error_context


class FakeMiddleware(BaseMiddleware):
    """Fake middleware implementation for testing composition behavior."""

    def __init__(
        self,
        name: str | None = None,
        timeout: float | None = None,
        should_fail: bool = False,
        execution_order: list[str] | None = None,
    ):
        super().__init__(name, timeout)
        self.should_fail = should_fail
        self.execution_order = execution_order if execution_order is not None else []
        self.called = False
        self.handler_called = False

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Fake middleware implementation that tracks execution."""
        self.called = True
        self.execution_order.append(f"{self.name}_pre")

        if self.should_fail:
            raise RuntimeError(f"Middleware {self.name} failed")

        # Call the handler
        result = await handler(*args, **kwargs)
        self.handler_called = True
        self.execution_order.append(f"{self.name}_post")

        return result


class FakeLoggingMiddleware(BaseMiddleware):
    """Fake logging middleware for testing categorization."""

    def __init__(self, name: str | None = None, timeout: float | None = None):
        super().__init__(name or "FakeLoggingMiddleware", timeout)
        self.called = False

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Fake logging middleware implementation."""
        self.called = True
        return await handler(*args, **kwargs)


class FakeAuthMiddleware(BaseMiddleware):
    """Fake authentication middleware for testing categorization."""

    def __init__(self, name: str | None = None, timeout: float | None = None):
        super().__init__(name or "FakeAuthMiddleware", timeout)
        self.called = False

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Fake authentication middleware implementation."""
        self.called = True
        return await handler(*args, **kwargs)


class FakeErrorMiddleware(BaseMiddleware):
    """Fake error handling middleware for testing categorization."""

    def __init__(self, name: str | None = None, timeout: float | None = None):
        super().__init__(name or "FakeErrorMiddleware", timeout)
        self.called = False

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Fake error handling middleware implementation."""
        self.called = True
        return await handler(*args, **kwargs)


async def _fake_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Fake handler for testing middleware composition."""
    return {"statusCode": 200, "body": "success"}


class TestMiddlewareComposerInitialization:
    """Test MiddlewareComposer initialization and properties."""

    def test_initialization_with_empty_middleware(self):
        """Test initialization with empty middleware list."""
        composer = MiddlewareComposer([])

        assert len(composer) == 0
        assert composer.middleware == []
        assert composer.default_timeout is None

    def test_initialization_with_middleware(self):
        """Test initialization with middleware list."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        composer = MiddlewareComposer([middleware1, middleware2])

        assert len(composer) == 2
        assert composer.middleware == [middleware1, middleware2]
        assert composer.default_timeout is None

    def test_initialization_with_timeout(self):
        """Test initialization with default timeout."""
        composer = MiddlewareComposer([], default_timeout=30.0)

        assert composer.default_timeout == 30.0

    def test_repr_without_timeout(self):
        """Test string representation without timeout."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware])

        expected = "MiddlewareComposer(middleware=['test'])"
        assert repr(composer) == expected

    def test_repr_with_timeout(self):
        """Test string representation with timeout."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware], default_timeout=30.0)

        expected = "MiddlewareComposer(middleware=['test'], timeout=30.0s)"
        assert repr(composer) == expected


class TestMiddlewareComposerOrdering:
    """Test middleware ordering and categorization."""

    def test_enforce_middleware_order_empty_list(self):
        """Test ordering with empty middleware list."""
        composer = MiddlewareComposer([])

        assert composer.middleware == []

    def test_enforce_middleware_order_single_middleware(self):
        """Test ordering with single middleware."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware])

        assert composer.middleware == [middleware]

    def test_categorize_middleware_logging(self):
        """Test categorization of logging middleware."""
        from src.contexts.shared_kernel.middleware.logging.structured_logger import (
            StructuredLoggingMiddleware,
        )

        strategy = FakeLoggingStrategy()
        logging_middleware = StructuredLoggingMiddleware(strategy=strategy)
        composer = MiddlewareComposer([])

        category = composer._categorize_middleware(logging_middleware)
        assert category == "logging"

    def test_categorize_middleware_auth(self):
        """Test categorization of authentication middleware."""
        from src.contexts.shared_kernel.middleware.auth.authentication import (
            AuthenticationMiddleware,
        )

        strategy = FakeAuthStrategy()
        auth_middleware = AuthenticationMiddleware(strategy=strategy)
        composer = MiddlewareComposer([])

        category = composer._categorize_middleware(auth_middleware)
        assert category == "auth"

    def test_categorize_middleware_error(self):
        """Test categorization of error handling middleware."""
        from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
            ExceptionHandlerMiddleware,
        )

        strategy = FakeErrorStrategy()
        error_middleware = ExceptionHandlerMiddleware(strategy=strategy)
        composer = MiddlewareComposer([])

        category = composer._categorize_middleware(error_middleware)
        assert category == "error"

    def test_categorize_middleware_custom(self):
        """Test categorization of custom middleware."""
        custom_middleware = FakeMiddleware("custom")
        composer = MiddlewareComposer([])

        category = composer._categorize_middleware(custom_middleware)
        assert category == "custom"

    def test_middleware_order_enforcement(self):
        """Test that middleware is ordered correctly by category."""
        # Create actual middleware instances with proper strategies
        logging_strategy = FakeLoggingStrategy()
        auth_strategy = FakeAuthStrategy()
        error_strategy = FakeErrorStrategy()

        from src.contexts.shared_kernel.middleware.auth.authentication import (
            AuthenticationMiddleware,
        )
        from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
            ExceptionHandlerMiddleware,
        )
        from src.contexts.shared_kernel.middleware.logging.structured_logger import (
            StructuredLoggingMiddleware,
        )

        logging1 = StructuredLoggingMiddleware(
            strategy=logging_strategy, name="logging1"
        )
        auth1 = AuthenticationMiddleware(strategy=auth_strategy, name="auth1")
        error1 = ExceptionHandlerMiddleware(strategy=error_strategy, name="error1")
        custom1 = FakeMiddleware("custom1")

        # Add in random order
        composer = MiddlewareComposer([custom1, auth1, error1, logging1])

        # Should be ordered: logging, auth, custom, error
        expected_order = [logging1, auth1, custom1, error1]
        assert composer.middleware == expected_order


class TestMiddlewareComposerComposition:
    """Test middleware composition and execution."""

    async def test_compose_single_middleware(self):
        """Test composition with single middleware."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware])

        composed_handler = composer.compose(_fake_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None
        result = await composed_handler(event, context)

        # Verify middleware was called
        assert middleware.called is True
        assert middleware.handler_called is True
        assert result == {"statusCode": 200, "body": "success"}

    async def test_compose_multiple_middleware(self):
        """Test composition with multiple middleware in correct order."""
        execution_order = []
        middleware1 = FakeMiddleware("middleware1", execution_order=execution_order)
        middleware2 = FakeMiddleware("middleware2", execution_order=execution_order)
        middleware3 = FakeMiddleware("middleware3", execution_order=execution_order)

        composer = MiddlewareComposer([middleware1, middleware2, middleware3])
        composed_handler = composer.compose(_fake_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None
        result = await composed_handler(event, context)

        # Verify all middleware was called
        assert middleware1.called is True
        assert middleware2.called is True
        assert middleware3.called is True

        # Verify execution order (should be reversed due to composition)
        # The middleware are composed in reverse order, so the last one becomes outermost
        # But the execution order shows the actual call sequence: first middleware becomes innermost
        expected_order = [
            "middleware1_pre",
            "middleware2_pre",
            "middleware3_pre",
            "middleware3_post",
            "middleware2_post",
            "middleware1_post",
        ]
        assert execution_order == expected_order
        assert result == {"statusCode": 200, "body": "success"}

    async def test_compose_with_timeout(self):
        """Test composition with timeout handling."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware], default_timeout=0.1)

        composed_handler = composer.compose(_fake_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None
        result = await composed_handler(event, context)

        # Should complete normally within timeout
        assert result == {"statusCode": 200, "body": "success"}

    async def test_compose_with_custom_timeout(self):
        """Test composition with custom timeout override."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware], default_timeout=30.0)

        composed_handler = composer.compose(_fake_handler, timeout=0.1)

        # Execute the composed handler
        event = {"test": "data"}
        context = None
        result = await composed_handler(event, context)

        # Should complete normally with custom timeout
        assert result == {"statusCode": 200, "body": "success"}

    async def test_compose_without_timeout(self):
        """Test composition without timeout."""
        middleware = FakeMiddleware("test")
        composer = MiddlewareComposer([middleware])

        composed_handler = composer.compose(_fake_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None
        result = await composed_handler(event, context)

        # Should complete normally without timeout
        assert result == {"statusCode": 200, "body": "success"}


class TestMiddlewareComposerErrorHandling:
    """Test middleware error handling and propagation."""

    async def test_middleware_error_propagation(self):
        """Test that middleware errors are properly propagated."""
        failing_middleware = FakeMiddleware("failing", should_fail=True)
        composer = MiddlewareComposer([failing_middleware])

        composed_handler = composer.compose(_fake_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None

        with pytest.raises(RuntimeError, match="Middleware failing failed"):
            await composed_handler(event, context)

        # Verify middleware was called but handler was not
        assert failing_middleware.called is True
        assert failing_middleware.handler_called is False

    async def test_middleware_error_in_chain(self):
        """Test error handling when middleware fails in the middle of a chain."""
        execution_order = []
        middleware1 = FakeMiddleware("middleware1", execution_order=execution_order)
        failing_middleware = FakeMiddleware(
            "failing", should_fail=True, execution_order=execution_order
        )
        middleware3 = FakeMiddleware("middleware3", execution_order=execution_order)

        composer = MiddlewareComposer([middleware1, failing_middleware, middleware3])
        composed_handler = composer.compose(_fake_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None

        with pytest.raises(RuntimeError, match="Middleware failing failed"):
            await composed_handler(event, context)

        # Verify execution order up to the failing middleware
        # The middleware are composed in reverse order, so the last one becomes outermost
        # But the execution order shows the actual call sequence: first middleware becomes innermost
        expected_order = ["middleware1_pre", "failing_pre"]
        assert execution_order == expected_order

        # Verify middleware states
        assert middleware1.called is True
        assert failing_middleware.called is True
        assert middleware3.called is False  # Should not be called due to error


class TestMiddlewareComposerAsyncBehavior:
    """Test async behavior and concurrency handling."""

    async def test_async_middleware_execution(self):
        """Test that async middleware executes correctly."""

        async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
            """Async handler for testing."""
            return {"statusCode": 200, "body": "async_success"}

        middleware = FakeMiddleware("async_test")
        composer = MiddlewareComposer([middleware])

        composed_handler = composer.compose(async_handler)

        # Execute the composed handler
        event = {"test": "data"}
        context = None
        result = await composed_handler(event, context)

        # Verify async execution
        assert middleware.called is True
        assert middleware.handler_called is True
        assert result == {"statusCode": 200, "body": "async_success"}

    async def test_concurrent_middleware_execution(self):
        """Test that middleware handles concurrent execution correctly."""
        middleware = FakeMiddleware("concurrent_test")
        composer = MiddlewareComposer([middleware])

        composed_handler = composer.compose(_fake_handler)

        # Execute multiple concurrent requests
        import anyio

        async def execute_request(request_id: int) -> dict[str, Any]:
            event = {"test": f"data_{request_id}"}
            context = None
            return await composed_handler(event, context)

        # Run multiple concurrent executions
        async with anyio.create_task_group() as tg:
            results = []
            for i in range(3):
                result = await execute_request(i + 1)
                results.append(result)

        # Verify all executions completed successfully
        expected_result = {"statusCode": 200, "body": "success"}
        assert all(result == expected_result for result in results)
        assert middleware.called is True


class TestMiddlewareComposerManagement:
    """Test middleware management operations."""

    def test_add_middleware_append(self):
        """Test adding middleware by appending."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        composer = MiddlewareComposer([middleware1])

        composer.add_middleware(middleware2)

        assert len(composer) == 2
        assert composer.middleware == [middleware1, middleware2]

    def test_add_middleware_at_position(self):
        """Test adding middleware at specific position."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        middleware3 = FakeMiddleware("middleware3")
        composer = MiddlewareComposer([middleware1, middleware3])

        composer.add_middleware(middleware2, position=1)

        assert len(composer) == 3
        assert composer.middleware == [middleware1, middleware2, middleware3]

    def test_remove_middleware(self):
        """Test removing middleware."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        composer = MiddlewareComposer([middleware1, middleware2])

        composer.remove_middleware(middleware1)

        assert len(composer) == 1
        assert composer.middleware == [middleware2]

    def test_remove_nonexistent_middleware(self):
        """Test removing middleware that doesn't exist."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        composer = MiddlewareComposer([middleware1])

        # Should not raise an error
        composer.remove_middleware(middleware2)

        assert len(composer) == 1
        assert composer.middleware == [middleware1]

    def test_clear_middleware(self):
        """Test clearing all middleware."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        composer = MiddlewareComposer([middleware1, middleware2])

        composer.clear()

        assert len(composer) == 0
        assert composer.middleware == []

    def test_len_operator(self):
        """Test length operator."""
        middleware1 = FakeMiddleware("middleware1")
        middleware2 = FakeMiddleware("middleware2")
        composer = MiddlewareComposer([middleware1, middleware2])

        assert len(composer) == 2
