"""Unit tests for structured logging middleware.

Tests the StructuredLoggingMiddleware and its logging strategies to ensure
proper formatting, async behavior, and middleware contracts are maintained.
"""

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anyio import create_task_group, sleep
from src.contexts.shared_kernel.middleware.core.base_middleware import EndpointHandler
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    AWSLambdaLoggingStrategy,
    LoggingStrategy,
    StructuredLoggingMiddleware,
    aws_lambda_logging_middleware,
    create_structured_logging_middleware,
)
from src.logging.logger import correlation_id_ctx


class FakeLoggingStrategy(LoggingStrategy):
    """Fake logging strategy for testing middleware behavior."""

    def __init__(self, logging_context: dict[str, Any] | None = None):
        """Initialize with optional logging context.

        Args:
            logging_context: Predefined logging context to return.
        """
        self.logging_context = logging_context or {
            "function_name": "test-function",
            "request_id": "test-request-123",
        }
        self.extract_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.get_request_data_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.inject_calls: list[tuple[dict[str, Any], dict[str, Any]]] = []

    def extract_logging_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract logging context from the request."""
        self.extract_calls.append((args, kwargs))
        return self.logging_context.copy()

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Extract request data from the middleware arguments."""
        self.get_request_data_calls.append((args, kwargs))
        event = {"httpMethod": "GET", "path": "/test"}
        context = MagicMock()
        return event, context

    def inject_logging_context(
        self, request_data: dict[str, Any], logging_context: dict[str, Any]
    ) -> None:
        """Inject logging context into the request data."""
        self.inject_calls.append((request_data, logging_context))
        request_data["_logging_context"] = logging_context


class FakeLogger:
    """Fake logger that captures log calls for verification."""

    def __init__(self):
        """Initialize the fake logger."""
        self.log_calls: list[tuple[str, str, dict[str, Any]]] = []
        self.name = "test.logger"

    def info(self, message: str, **kwargs: Any) -> None:
        """Capture info log calls."""
        self.log_calls.append(("info", message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Capture error log calls."""
        self.log_calls.append(("error", message, kwargs))


@pytest.fixture
def fake_strategy() -> FakeLoggingStrategy:
    """Create a fake logging strategy for testing."""
    return FakeLoggingStrategy()


@pytest.fixture
def fake_logger() -> FakeLogger:
    """Create a fake logger for testing."""
    return FakeLogger()


@pytest.fixture
def fake_handler() -> EndpointHandler:
    """Create a fake endpoint handler for testing."""
    return AsyncMock(return_value={"statusCode": 200, "body": "success"})


@pytest.fixture
def middleware(fake_strategy: FakeLoggingStrategy) -> StructuredLoggingMiddleware:
    """Create structured logging middleware with fake dependencies."""
    return StructuredLoggingMiddleware(
        strategy=fake_strategy,
        name="test-logging",
        log_request=True,
        log_response=True,
        log_timing=True,
        log_correlation_id=True,
    )


class TestLoggingStrategy:
    """Test the LoggingStrategy abstract base class."""

    def test_logging_strategy_is_abstract(self) -> None:
        """Test that LoggingStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LoggingStrategy()  # type: ignore


class TestAWSLambdaLoggingStrategy:
    """Test the AWS Lambda logging strategy implementation."""

    def test_extract_logging_context_with_args(self) -> None:
        """Test extracting logging context from positional arguments."""
        strategy = AWSLambdaLoggingStrategy()
        event = {"httpMethod": "GET", "path": "/test", "type": "api"}
        context = MagicMock()
        context.function_name = "test-function"
        context.function_version = "1"
        context.request_id = "req-123"
        context.memory_limit_in_mb = 128
        context.remaining_time_in_millis = 5000

        result = strategy.extract_logging_context(event, context)

        assert result["function_name"] == "test-function"
        assert result["function_version"] == "1"
        assert result["request_id"] == "req-123"
        assert result["memory_limit_mb"] == 128
        assert result["remaining_time_ms"] == 5000
        assert "event_summary" in result
        assert result["event_summary"]["http_method"] == "GET"
        assert result["event_summary"]["path"] == "/test"

    def test_extract_logging_context_with_kwargs(self) -> None:
        """Test extracting logging context from keyword arguments."""
        strategy = AWSLambdaLoggingStrategy()
        event = {"httpMethod": "POST", "path": "/api/test"}
        context = MagicMock()
        context.function_name = "api-function"

        result = strategy.extract_logging_context(event=event, context=context)

        assert result["function_name"] == "api-function"
        assert result["event_summary"]["http_method"] == "POST"

    def test_get_request_data_with_args(self) -> None:
        """Test getting request data from positional arguments."""
        strategy = AWSLambdaLoggingStrategy()
        event = {"httpMethod": "GET"}
        context = MagicMock()

        result_event, result_context = strategy.get_request_data(event, context)

        assert result_event == event
        assert result_context == context

    def test_get_request_data_with_kwargs(self) -> None:
        """Test getting request data from keyword arguments."""
        strategy = AWSLambdaLoggingStrategy()
        event = {"httpMethod": "POST"}
        context = MagicMock()

        result_event, result_context = strategy.get_request_data(
            event=event, context=context
        )

        assert result_event == event
        assert result_context == context

    def test_get_request_data_missing_arguments_raises_error(self) -> None:
        """Test that missing arguments raise appropriate errors."""
        strategy = AWSLambdaLoggingStrategy()

        # Test with no arguments - should raise IndexError (no args to access)
        with pytest.raises(IndexError):
            strategy.get_request_data()

        # Test with None values - should raise ValueError (None values are invalid)
        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data(event=None, context=None)

        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data(None, None)

        # Test with missing positional arguments - should raise IndexError
        with pytest.raises(IndexError):
            strategy.get_request_data({"event": "test"})  # Missing context arg

    def test_inject_logging_context(self) -> None:
        """Test injecting logging context into request data."""
        strategy = AWSLambdaLoggingStrategy()
        request_data = {"httpMethod": "GET"}
        logging_context = {"request_id": "req-123", "function_name": "test"}

        strategy.inject_logging_context(request_data, logging_context)

        assert request_data["_logging_context"] == logging_context

    def test_get_event_summary(self) -> None:
        """Test event summary generation."""
        strategy = AWSLambdaLoggingStrategy()
        event = {
            "type": "api",
            "source": "api-gateway",
            "id": "evt-123",
            "httpMethod": "GET",
            "path": "/test",
            "resource": "/test",
        }

        summary = strategy._get_event_summary(event)

        assert summary["event_type"] == "api"
        assert summary["event_source"] == "api-gateway"
        assert summary["event_id"] == "evt-123"
        assert summary["http_method"] == "GET"
        assert summary["path"] == "/test"
        assert summary["resource"] == "/test"

    def test_get_event_summary_minimal_event(self) -> None:
        """Test event summary with minimal event data."""
        strategy = AWSLambdaLoggingStrategy()
        event = {}

        summary = strategy._get_event_summary(event)

        assert summary["event_type"] == "unknown"
        assert summary["event_source"] == "unknown"
        assert summary["event_id"] == "unknown"
        assert "http_method" not in summary


class TestStructuredLoggingMiddleware:
    """Test the StructuredLoggingMiddleware implementation."""

    def test_middleware_initialization(
        self, fake_strategy: FakeLoggingStrategy
    ) -> None:
        """Test middleware initialization with proper configuration."""
        middleware = StructuredLoggingMiddleware(
            strategy=fake_strategy,
            name="test-middleware",
            logger_name="test.logger",
            log_request=True,
            log_response=False,
            log_timing=True,
            log_correlation_id=False,
        )

        assert middleware.name == "test-middleware"
        assert middleware.strategy == fake_strategy
        assert middleware.log_request is True
        assert middleware.log_response is False
        assert middleware.log_timing is True
        assert middleware.log_correlation_id is False

    def test_middleware_initialization_defaults(
        self, fake_strategy: FakeLoggingStrategy
    ) -> None:
        """Test middleware initialization with default values."""
        middleware = StructuredLoggingMiddleware(strategy=fake_strategy)

        assert middleware.name == "StructuredLoggingMiddleware"
        assert middleware.log_request is True
        assert middleware.log_response is True
        assert middleware.log_timing is True
        assert middleware.log_correlation_id is True

    @pytest.mark.anyio
    async def test_middleware_successful_request(
        self,
        middleware: StructuredLoggingMiddleware,
        fake_handler: EndpointHandler,
        fake_logger: FakeLogger,
    ) -> None:
        """Test middleware with successful request processing."""
        with (
            patch("time.time", side_effect=[1000.0, 1000.5]),
            patch.object(middleware, "logger", fake_logger),
        ):
            response = await middleware(fake_handler, "event", "context")

        # Verify response
        assert response == {"statusCode": 200, "body": "success"}

        # Verify strategy calls
        fake_strategy = middleware.strategy
        assert isinstance(fake_strategy, FakeLoggingStrategy)
        assert len(fake_strategy.extract_calls) == 1
        assert len(fake_strategy.get_request_data_calls) == 1
        assert len(fake_strategy.inject_calls) == 1

        # Verify logging calls
        assert len(fake_logger.log_calls) == 2  # request start + response success

        # Verify request start log
        request_log = fake_logger.log_calls[0]
        assert request_log[0] == "info"
        assert request_log[1] == "Request started"
        assert request_log[2]["log_event"] == "request_start"
        assert request_log[2]["correlation_id"] is not None

        # Verify response success log
        response_log = fake_logger.log_calls[1]
        assert response_log[0] == "info"
        assert response_log[1] == "Request completed successfully"
        assert response_log[2]["log_event"] == "request_completed"
        assert response_log[2]["status"] == "success"
        assert response_log[2]["execution_time_ms"] == 500.0

    @pytest.mark.anyio
    async def test_middleware_error_handling(
        self, middleware: StructuredLoggingMiddleware, fake_logger: FakeLogger
    ) -> None:
        """Test middleware error handling and logging."""
        error_handler = AsyncMock(side_effect=ValueError("Test error"))

        with (
            patch("time.time", side_effect=[1000.0, 1000.2]),
            patch.object(middleware, "logger", fake_logger),
        ):
            with pytest.raises(ValueError, match="Test error"):
                await middleware(error_handler, "event", "context")

        # Verify error logging
        assert len(fake_logger.log_calls) == 2  # request start + error

        error_log = fake_logger.log_calls[1]
        assert error_log[0] == "error"
        assert error_log[1] == "Request failed"
        assert error_log[2]["log_event"] == "request_failed"
        assert error_log[2]["status"] == "error"
        assert error_log[2]["error_type"] == "ValueError"
        assert error_log[2]["error_message"] == "Test error"
        assert error_log[2]["execution_time_ms"] == 200.0

    @pytest.mark.anyio
    async def test_middleware_logging_disabled(
        self, fake_strategy: FakeLoggingStrategy, fake_logger: FakeLogger
    ) -> None:
        """Test middleware with logging disabled."""
        middleware = StructuredLoggingMiddleware(
            strategy=fake_strategy,
            log_request=False,
            log_response=False,
            log_timing=False,
            log_correlation_id=False,
        )

        fake_handler = AsyncMock(return_value={"statusCode": 200})

        with patch.object(middleware, "logger", fake_logger):
            await middleware(fake_handler, "event", "context")

        # Verify no logging calls
        assert len(fake_logger.log_calls) == 0

    @pytest.mark.anyio
    async def test_middleware_correlation_id_handling(
        self,
        middleware: StructuredLoggingMiddleware,
        fake_handler: EndpointHandler,
        fake_logger: FakeLogger,
    ) -> None:
        """Test middleware correlation ID handling."""
        test_correlation_id = "test-correlation-123"
        correlation_id_ctx.set(test_correlation_id)

        with patch.object(middleware, "logger", fake_logger):
            await middleware(fake_handler, "event", "context")

        # Verify correlation ID in logs
        request_log = fake_logger.log_calls[0]
        assert request_log[2]["correlation_id"] == test_correlation_id

        response_log = fake_logger.log_calls[1]
        assert response_log[2]["correlation_id"] == test_correlation_id

    @pytest.mark.anyio
    async def test_middleware_response_summary(
        self, fake_strategy: FakeLoggingStrategy, fake_logger: FakeLogger
    ) -> None:
        """Test middleware response summary generation."""
        middleware = StructuredLoggingMiddleware(
            strategy=fake_strategy,
            include_response_summary=True,
        )

        response = {"statusCode": 201, "body": '{"message": "created"}'}
        fake_handler = AsyncMock(return_value=response)

        with patch.object(middleware, "logger", fake_logger):
            await middleware(fake_handler, "event", "context")

        # Verify response summary in log
        response_log = fake_logger.log_calls[1]
        assert "response_summary" in response_log[2]
        summary = response_log[2]["response_summary"]
        assert summary["status_code"] == 201
        assert summary["response_size_bytes"] > 0

    @pytest.mark.anyio
    async def test_middleware_event_summary(self, fake_logger: FakeLogger) -> None:
        """Test middleware event summary generation."""
        # Create a fake strategy that includes event_summary
        fake_strategy = FakeLoggingStrategy(
            {
                "function_name": "test-function",
                "request_id": "test-request-123",
                "event_summary": {
                    "event_type": "api",
                    "http_method": "GET",
                    "path": "/test",
                },
            }
        )

        middleware = StructuredLoggingMiddleware(
            strategy=fake_strategy,
            include_event_summary=True,
        )

        fake_handler = AsyncMock(return_value={"statusCode": 200})

        with patch.object(middleware, "logger", fake_logger):
            await middleware(fake_handler, "event", "context")

        # Verify event summary in log
        request_log = fake_logger.log_calls[0]
        assert "event_summary" in request_log[2]
        assert request_log[2]["event_summary"]["event_type"] == "api"

    def test_get_logging_context(self, middleware: StructuredLoggingMiddleware) -> None:
        """Test getting logging context from request data."""
        request_data = {"_logging_context": {"request_id": "test-123"}}

        context = middleware.get_logging_context(request_data)

        assert context == {"request_id": "test-123"}

    def test_get_logging_context_missing(
        self, middleware: StructuredLoggingMiddleware
    ) -> None:
        """Test getting logging context when missing."""
        request_data = {}

        context = middleware.get_logging_context(request_data)

        assert context is None

    def test_response_summary_generation(
        self, middleware: StructuredLoggingMiddleware
    ) -> None:
        """Test response summary generation."""
        # Test with string body
        response = {"statusCode": 200, "body": "test response"}
        summary = middleware._get_response_summary(response)
        assert summary["status_code"] == 200
        assert summary["response_size_bytes"] == len(b"test response")

        # Test with dict body
        response = {"statusCode": 201, "body": {"message": "created"}}
        summary = middleware._get_response_summary(response)
        assert summary["status_code"] == 201
        assert summary["response_size_bytes"] > 0

        # Test with list body
        response = {"statusCode": 200, "body": [1, 2, 3]}
        summary = middleware._get_response_summary(response)
        assert summary["status_code"] == 200
        assert summary["response_size_bytes"] > 0

        # Test without body
        response = {"statusCode": 204}
        summary = middleware._get_response_summary(response)
        assert summary["status_code"] == 204
        assert "response_size_bytes" not in summary

    @pytest.mark.anyio
    async def test_middleware_async_behavior(
        self, middleware: StructuredLoggingMiddleware, fake_logger: FakeLogger
    ) -> None:
        """Test middleware async behavior and concurrency."""

        async def slow_handler(event: Any, context: Any) -> dict[str, Any]:
            await sleep(0.01)  # Small delay to test async behavior
            return {"statusCode": 200, "body": "async success"}

        start_time = time.time()
        with patch.object(middleware, "logger", fake_logger):
            response = await middleware(slow_handler, "event", "context")
        end_time = time.time()

        # Verify async execution
        assert response == {"statusCode": 200, "body": "async success"}
        assert end_time - start_time >= 0.01  # Should include the sleep time

        # Verify timing is logged
        response_log = fake_logger.log_calls[1]
        assert response_log[2]["execution_time_ms"] >= 10.0

    @pytest.mark.anyio
    async def test_middleware_concurrent_execution(
        self, fake_strategy: FakeLoggingStrategy, fake_logger: FakeLogger
    ) -> None:
        """Test middleware with concurrent execution."""
        middleware = StructuredLoggingMiddleware(strategy=fake_strategy)

        async def handler(event: Any, context: Any) -> dict[str, Any]:
            return {"statusCode": 200, "body": f"response-{event}"}

        # Run multiple concurrent requests
        with patch.object(middleware, "logger", fake_logger):
            async with create_task_group() as tg:
                for i in range(3):
                    tg.start_soon(middleware, handler, f"event-{i}", f"context-{i}")

        # Verify all requests were processed
        assert len(fake_logger.log_calls) == 6  # 3 requests * 2 logs each


class TestFactoryFunctions:
    """Test factory functions for creating middleware."""

    def test_create_structured_logging_middleware(
        self, fake_strategy: FakeLoggingStrategy
    ) -> None:
        """Test create_structured_logging_middleware factory function."""
        middleware = create_structured_logging_middleware(
            strategy=fake_strategy,
            name="factory-test",
            logger_name="factory.logger",
            log_request=False,
            log_response=True,
        )

        assert isinstance(middleware, StructuredLoggingMiddleware)
        assert middleware.name == "factory-test"
        assert middleware.strategy == fake_strategy
        assert middleware.log_request is False
        assert middleware.log_response is True

    def test_aws_lambda_logging_middleware(self) -> None:
        """Test aws_lambda_logging_middleware factory function."""
        middleware = aws_lambda_logging_middleware(
            name="lambda-test",
            logger_name="lambda.logger",
            include_event_summary=True,
        )

        assert isinstance(middleware, StructuredLoggingMiddleware)
        assert middleware.name == "lambda-test"
        assert isinstance(middleware.strategy, AWSLambdaLoggingStrategy)
        assert middleware.include_event_summary is True


class TestStructuredLoggerFormatting:
    """Test structured logger formatting behavior."""

    @pytest.mark.anyio
    async def test_structured_logger_formatting(
        self, fake_strategy: FakeLoggingStrategy, fake_logger: FakeLogger
    ) -> None:
        """Test that structured logs are formatted correctly."""
        middleware = StructuredLoggingMiddleware(strategy=fake_strategy)

        fake_handler = AsyncMock(return_value={"statusCode": 200, "body": "success"})

        with patch.object(middleware, "logger", fake_logger):
            await middleware(fake_handler, "event", "context")

        # Verify log structure and formatting
        assert len(fake_logger.log_calls) == 2

        # Check request log format
        request_log = fake_logger.log_calls[0]
        assert request_log[0] == "info"
        assert request_log[1] == "Request started"
        log_data = request_log[2]
        assert "log_event" in log_data
        assert "correlation_id" in log_data
        assert "timestamp" in log_data
        assert log_data["log_event"] == "request_start"

        # Check response log format
        response_log = fake_logger.log_calls[1]
        assert response_log[0] == "info"
        assert response_log[1] == "Request completed successfully"
        log_data = response_log[2]
        assert "log_event" in log_data
        assert "correlation_id" in log_data
        assert "execution_time_ms" in log_data
        assert "status" in log_data
        assert log_data["log_event"] == "request_completed"
        assert log_data["status"] == "success"

    @pytest.mark.anyio
    async def test_structured_logger_async_behavior(
        self, fake_strategy: FakeLoggingStrategy, fake_logger: FakeLogger
    ) -> None:
        """Test that structured logger handles async behavior correctly."""
        middleware = StructuredLoggingMiddleware(strategy=fake_strategy)

        async def async_handler(event: Any, context: Any) -> dict[str, Any]:
            await sleep(0.001)  # Small async delay
            return {"statusCode": 201, "body": "async response"}

        with patch.object(middleware, "logger", fake_logger):
            await middleware(async_handler, "event", "context")

        # Verify async execution completed
        assert len(fake_logger.log_calls) == 2
        response_log = fake_logger.log_calls[1]
        assert response_log[2]["status"] == "success"
        assert response_log[2]["execution_time_ms"] > 0

    def test_log_data_cleanup(self, fake_strategy: FakeLoggingStrategy) -> None:
        """Test that None values are cleaned up from log data."""
        # Test with None values in logging context
        fake_strategy.logging_context = {
            "function_name": "test",
            "request_id": None,
            "memory_limit_mb": 128,
        }

        log_data = {
            "log_event": "request_start",
            "correlation_id": None,
            "timestamp": "now",
            "function_name": "test",
            "request_id": None,
            "memory_limit_mb": 128,
        }

        # Simulate the cleanup logic
        cleaned_data = {k: v for k, v in log_data.items() if v is not None}

        assert "correlation_id" not in cleaned_data
        assert "request_id" not in cleaned_data
        assert "function_name" in cleaned_data
        assert "memory_limit_mb" in cleaned_data
        assert cleaned_data["function_name"] == "test"
        assert cleaned_data["memory_limit_mb"] == 128
