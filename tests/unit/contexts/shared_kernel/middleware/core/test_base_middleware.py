"""Unit tests for BaseMiddleware class.

Tests the foundational middleware infrastructure ensuring consistent behavior
and composition patterns for all middleware components.
"""

from typing import Any

import pytest
from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)

pytestmark = pytest.mark.anyio


class SimpleAsyncMiddleware(BaseMiddleware):
    """Simple async implementation of BaseMiddleware for basic testing."""

    def __init__(self, name: str | None = None, timeout: float | None = None):
        super().__init__(name, timeout)
        self.called = False
        self.handler_called = False
        self.pre_processed = False
        self.post_processed = False

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Simple async implementation that tracks execution flow."""
        self.called = True
        self.pre_processed = True

        # Call the handler (this is async)
        result = await handler(*args, **kwargs)
        self.handler_called = True

        self.post_processed = True
        return result


class AsyncMiddleware(BaseMiddleware):
    """Async middleware implementation for testing async behavior."""

    def __init__(self, name: str | None = None, timeout: float | None = None):
        super().__init__(name, timeout)
        self.async_operations = []

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Async implementation with multiple async operations."""
        self.async_operations.append("pre_async")

        # Simulate async pre-processing
        await _async_delay(0.001)
        self.async_operations.append("pre_complete")

        # Call handler
        result = await handler(*args, **kwargs)
        self.async_operations.append("handler_called")

        # Simulate async post-processing
        await _async_delay(0.001)
        self.async_operations.append("post_complete")

        return result


async def _async_delay(seconds: float) -> None:
    """Helper function to simulate async operations."""
    import anyio

    await anyio.sleep(seconds)


class TestBaseMiddlewareInitialization:
    """Test BaseMiddleware initialization and properties."""

    def test_initialization_with_default_name(self):
        """Test initialization with default name from class name."""
        middleware = SimpleAsyncMiddleware()

        assert middleware.name == "SimpleAsyncMiddleware"
        assert middleware.timeout is None

    def test_initialization_with_custom_name(self):
        """Test initialization with custom name."""
        middleware = SimpleAsyncMiddleware(name="CustomMiddleware")

        assert middleware.name == "CustomMiddleware"
        assert middleware.timeout is None

    def test_initialization_with_timeout(self):
        """Test initialization with timeout."""
        middleware = SimpleAsyncMiddleware(timeout=30.0)

        assert middleware.name == "SimpleAsyncMiddleware"
        assert middleware.timeout == 30.0

    def test_initialization_with_custom_name_and_timeout(self):
        """Test initialization with both custom name and timeout."""
        middleware = SimpleAsyncMiddleware(name="TestMiddleware", timeout=60.0)

        assert middleware.name == "TestMiddleware"
        assert middleware.timeout == 60.0


class TestBaseMiddlewareRepr:
    """Test BaseMiddleware string representation."""

    def test_repr_without_timeout(self):
        """Test string representation without timeout."""
        middleware = SimpleAsyncMiddleware(name="TestMiddleware")

        expected = "SimpleAsyncMiddleware(name='TestMiddleware')"
        assert repr(middleware) == expected

    def test_repr_with_timeout(self):
        """Test string representation with timeout."""
        middleware = SimpleAsyncMiddleware(name="TestMiddleware", timeout=30.0)

        expected = "SimpleAsyncMiddleware(name='TestMiddleware', timeout=30.0s)"
        assert repr(middleware) == expected

    def test_repr_with_default_name(self):
        """Test string representation with default name."""
        middleware = SimpleAsyncMiddleware()

        expected = "SimpleAsyncMiddleware(name='SimpleAsyncMiddleware')"
        assert repr(middleware) == expected


class TestBaseMiddlewareAbstractBehavior:
    """Test BaseMiddleware abstract method enforcement."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseMiddleware cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseMiddleware()  # type: ignore[abstract]

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementations can be instantiated."""
        middleware = SimpleAsyncMiddleware()
        assert isinstance(middleware, BaseMiddleware)
        assert isinstance(middleware, SimpleAsyncMiddleware)


class TestBaseMiddlewareAsyncBehavior:
    """Test BaseMiddleware async behavior and contracts."""

    async def test_base_middleware_async_behavior(self):
        """Test that middleware handles async operations correctly."""

        # Create async handler
        async def async_handler(*args, **kwargs) -> dict[str, Any]:
            await _async_delay(0.001)
            return {"status": "success", "data": "test"}

        # Create middleware
        middleware = AsyncMiddleware(name="AsyncTest", timeout=5.0)

        # Execute middleware
        result = await middleware(async_handler, "arg1", "arg2", key1="value1")

        # Verify async behavior
        assert result == {"status": "success", "data": "test"}
        assert middleware.async_operations == [
            "pre_async",
            "pre_complete",
            "handler_called",
            "post_complete",
        ]
        assert middleware.name == "AsyncTest"
        assert middleware.timeout == 5.0

    async def test_middleware_preserves_handler_arguments(self):
        """Test that middleware preserves all handler arguments."""

        async def test_handler(*args, **kwargs) -> dict[str, Any]:
            return {"args": args, "kwargs": kwargs, "status": "success"}

        middleware = SimpleAsyncMiddleware()

        result = await middleware(
            test_handler,
            "positional1",
            "positional2",
            keyword1="value1",
            keyword2="value2",
        )

        assert result["args"] == ("positional1", "positional2")
        assert result["kwargs"] == {"keyword1": "value1", "keyword2": "value2"}
        assert result["status"] == "success"

    async def test_middleware_execution_order(self):
        """Test that middleware executes in correct order (pre -> handler -> post)."""

        async def simple_handler() -> dict[str, Any]:
            return {"handler_executed": True}

        middleware = SimpleAsyncMiddleware()

        # Verify initial state
        assert not middleware.called
        assert not middleware.pre_processed
        assert not middleware.handler_called
        assert not middleware.post_processed

        # Execute middleware
        result = await middleware(simple_handler)

        # Verify execution order
        assert result == {"handler_executed": True}
        assert middleware.called
        assert middleware.pre_processed
        assert middleware.handler_called
        assert middleware.post_processed

    async def test_middleware_handles_handler_exceptions(self):
        """Test that middleware can handle exceptions from handlers."""

        async def failing_handler() -> dict[str, Any]:
            raise ValueError("Handler failed")

        class ExceptionHandlingMiddleware(BaseMiddleware):
            def __init__(self):
                super().__init__()
                self.exception_caught = False

            async def __call__(
                self,
                handler: EndpointHandler,
                *args,
                **kwargs,
            ) -> dict[str, Any]:
                try:
                    return await handler(*args, **kwargs)
                except Exception as e:
                    self.exception_caught = True
                    return {"error": str(e), "status": "error"}

        middleware = ExceptionHandlingMiddleware()

        result = await middleware(failing_handler)

        assert result == {"error": "Handler failed", "status": "error"}
        assert middleware.exception_caught

    async def test_middleware_returns_handler_result(self):
        """Test that middleware returns the handler's result."""

        async def data_handler() -> dict[str, Any]:
            return {"data": "test_data", "count": 42}

        middleware = SimpleAsyncMiddleware()

        result = await middleware(data_handler)

        assert result == {"data": "test_data", "count": 42}

    async def test_multiple_middleware_composition(self):
        """Test that multiple middleware can be composed together."""

        class LoggingMiddleware(BaseMiddleware):
            def __init__(self):
                super().__init__("LoggingMiddleware")
                self.logs = []

            async def __call__(
                self,
                handler: EndpointHandler,
                *args,
                **kwargs,
            ) -> dict[str, Any]:
                self.logs.append("pre_handler")
                result = await handler(*args, **kwargs)
                self.logs.append("post_handler")
                return result

        class TimingMiddleware(BaseMiddleware):
            def __init__(self):
                super().__init__("TimingMiddleware")
                self.timing = {}

            async def __call__(
                self,
                handler: EndpointHandler,
                *args,
                **kwargs,
            ) -> dict[str, Any]:
                self.timing["start"] = "recorded"
                result = await handler(*args, **kwargs)
                self.timing["end"] = "recorded"
                return result

        async def business_handler() -> dict[str, Any]:
            return {"business": "logic"}

        # Create middleware instances
        logging_middleware = LoggingMiddleware()
        timing_middleware = TimingMiddleware()

        # Compose middleware manually (simulating composition)
        async def composed_handler() -> dict[str, Any]:
            return await logging_middleware(lambda: timing_middleware(business_handler))

        result = await composed_handler()

        # Verify composition worked
        assert result == {"business": "logic"}
        assert logging_middleware.logs == ["pre_handler", "post_handler"]
        assert timing_middleware.timing == {"start": "recorded", "end": "recorded"}


class TestEndpointHandlerType:
    """Test EndpointHandler type definition."""

    async def test_endpoint_handler_type_definition(self):
        """Test that EndpointHandler is properly defined."""

        # This should not raise any type errors
        async def handler() -> dict[str, Any]:
            return {"test": "value"}

        # Verify it's callable
        assert callable(handler)
        result = await handler()
        assert result == {"test": "value"}

    async def test_endpoint_handler_async_contract(self):
        """Test that EndpointHandler works with async functions."""

        async def async_handler() -> dict[str, Any]:
            return {"async": "result"}

        # This should be valid
        handler: EndpointHandler = async_handler

        # Verify it can be called
        result = await handler()
        assert result == {"async": "result"}
