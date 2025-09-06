"""Unit tests for exception handler middleware.

Tests the ExceptionHandlerMiddleware and its error handling strategies
following the testing principles: no I/O, fakes for dependencies,
and behavior-focused assertions.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from src.contexts.shared_kernel.middleware.error_handling.error_response import (
    ErrorDetail,
    ErrorResponse,
    ErrorType,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    AWSLambdaErrorHandlingStrategy,
    ErrorHandlingStrategy,
    ExceptionHandlerMiddleware,
    aws_lambda_exception_handler_middleware,
    create_exception_handler_middleware,
)


# Test fixtures and fakes
class FakeErrorHandlingStrategy(ErrorHandlingStrategy):
    """Fake error handling strategy for testing."""

    def __init__(self, error_context: dict[str, Any] | None = None):
        self.error_context = error_context or {}
        self.extract_calls = []
        self.get_request_calls = []
        self.inject_calls = []

    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract error context from the request."""
        self.extract_calls.append((args, kwargs))
        return self.error_context

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Extract request data from the middleware arguments."""
        self.get_request_calls.append((args, kwargs))
        return {"test": "data"}, MagicMock()

    def inject_error_context(
        self, request_data: dict[str, Any], error_context: dict[str, Any]
    ) -> None:
        """Inject error context into the request data."""
        self.inject_calls.append((request_data, error_context))
        request_data["_error_context"] = error_context


class FakeLogger:
    """Fake logger for testing structured logging behavior."""

    def __init__(self):
        self.logs = []
        self.debug_calls = []
        self.warning_calls = []
        self.error_calls = []

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.debug_calls.append((message, kwargs))
        self.logs.append(("debug", message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.warning_calls.append((message, kwargs))
        self.logs.append(("warning", message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.error_calls.append((message, kwargs))
        self.logs.append(("error", message, kwargs))


@pytest.fixture
def fake_strategy():
    """Create a fake error handling strategy."""
    return FakeErrorHandlingStrategy()


@pytest.fixture
def fake_logger():
    """Create a fake logger."""
    return FakeLogger()


@pytest.fixture
def middleware(fake_strategy, fake_logger):
    """Create exception handler middleware with fake dependencies."""
    # Patch the logger creation to use our fake
    import src.contexts.shared_kernel.middleware.error_handling.exception_handler as module

    original_get_logger = module.StructlogFactory.get_logger
    module.StructlogFactory.get_logger = MagicMock(return_value=fake_logger)

    try:
        middleware = ExceptionHandlerMiddleware(
            strategy=fake_strategy,
            name="test_exception_handler",
            logger_name="test_logger",
            include_stack_trace=False,
            expose_internal_details=False,
            default_error_message="Test error occurred",
        )
        yield middleware
    finally:
        # Restore original method
        module.StructlogFactory.get_logger = original_get_logger


@pytest.fixture
def successful_handler():
    """Create a successful handler for testing."""

    async def handler(*args, **kwargs):
        return {"statusCode": 200, "body": "success"}

    return handler


@pytest.fixture
def failing_handler():
    """Create a failing handler for testing."""

    async def handler(*args, **kwargs):
        raise ValueError("Test validation error")

    return handler


@pytest.fixture
def validation_error_handler():
    """Create a handler that raises ValidationError."""

    async def handler(*args, **kwargs):
        # Create a simple ValidationError for testing
        try:
            from pydantic import BaseModel, Field

            class TestModel(BaseModel):
                field: str = Field(..., min_length=1)

            TestModel(field="")  # This will raise ValidationError
        except ValidationError as e:
            raise e

    return handler


@pytest.fixture
def exception_group_handler():
    """Create a handler that raises ExceptionGroup."""

    async def handler(*args, **kwargs):
        raise ExceptionGroup(
            "Multiple errors", [ValueError("Error 1"), TypeError("Error 2")]
        )

    return handler


# Test cases
class TestExceptionHandlerMiddleware:
    """Test ExceptionHandlerMiddleware behavior."""

    @pytest.mark.anyio
    async def test_successful_request_logging(
        self, middleware, successful_handler, fake_logger
    ):
        """Test that successful requests are logged at debug level."""
        # Given
        event = {"test": "data"}
        context = MagicMock()

        # When
        result = await middleware(successful_handler, event, context=context)

        # Then
        assert result == {"statusCode": 200, "body": "success"}
        assert len(fake_logger.debug_calls) == 1
        debug_call = fake_logger.debug_calls[0]
        assert "Request processed successfully" in debug_call[0]
        assert debug_call[1]["middleware_name"] == "test_exception_handler"
        assert debug_call[1]["handler_name"] == "handler"

    @pytest.mark.anyio
    async def test_single_exception_error_mapping(
        self, middleware, failing_handler, fake_strategy
    ):
        """Test that single exceptions are mapped to appropriate error responses."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(failing_handler, event, context=context)

        # Then
        assert result["status_code"] == 422  # VALIDATION_ERROR status
        assert result["error_type"] == "validation_error"
        assert result["message"] == "Test validation error"
        assert result["detail"] == "Test validation error"
        assert result["correlation_id"] is not None
        assert "timestamp" in result
        assert len(fake_strategy.extract_calls) == 1

    @pytest.mark.anyio
    async def test_validation_error_with_details(
        self, middleware, validation_error_handler, fake_strategy
    ):
        """Test that ValidationError includes detailed error information."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(validation_error_handler, event, context=context)

        # Then
        assert result["status_code"] == 422
        assert result["error_type"] == "validation_error"
        # Should have a message (exact format is implementation detail)
        assert result["message"] is not None
        assert len(result["message"]) > 0
        # Should include detailed validation errors
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert result["errors"][0]["field"] == "field"
        assert result["errors"][0]["code"] == "string_too_short"
        assert result["errors"][0]["message"] is not None

    @pytest.mark.anyio
    async def test_exception_group_prioritization(
        self, middleware, exception_group_handler, fake_strategy
    ):
        """Test that exception groups prioritize validation errors."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(exception_group_handler, event, context=context)

        # Then
        assert result["status_code"] == 422  # First ValueError should be prioritized
        assert result["error_type"] == "validation_error"
        assert result["message"] == "Error 1"

    @pytest.mark.anyio
    async def test_exception_categorization(self, middleware, fake_strategy):
        """Test that different exception types are categorized correctly."""
        # Given
        test_cases = [
            (ValueError("test"), ErrorType.VALIDATION_ERROR, 422),
            (TypeError("test"), ErrorType.VALIDATION_ERROR, 422),
            (KeyError("test"), ErrorType.NOT_FOUND_ERROR, 404),
            (FileNotFoundError("test"), ErrorType.NOT_FOUND_ERROR, 404),
            (PermissionError("test"), ErrorType.AUTHORIZATION_ERROR, 403),
            (TimeoutError("test"), ErrorType.TIMEOUT_ERROR, 408),
            (ConnectionError("test"), ErrorType.TIMEOUT_ERROR, 408),
            (RuntimeError("test"), ErrorType.INTERNAL_ERROR, 500),
        ]

        for exc, expected_type, expected_status in test_cases:
            # Given
            async def handler(*args, **kwargs):
                raise exc

            event = {"test": "data"}
            context = MagicMock()
            fake_strategy.error_context = {"function_name": "test_function"}

            # When
            result = await middleware(handler, event, context=context)

            # Then
            assert result["error_type"] == expected_type.value
            assert result["status_code"] == expected_status

    @pytest.mark.anyio
    async def test_error_logging_behavior(
        self, middleware, failing_handler, fake_logger, fake_strategy
    ):
        """Test that errors are logged with appropriate level and structure."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {
            "function_name": "test_function",
            "request_id": "req-123",
        }

        # When
        result = await middleware(failing_handler, event, context=context)

        # Then
        # Should log warning for client error (4xx)
        assert len(fake_logger.warning_calls) == 1
        warning_call = fake_logger.warning_calls[0]
        assert "Client error handled" in warning_call[0]
        assert warning_call[1]["exception_type"] == "ValueError"
        assert warning_call[1]["exception_message"] == "Test validation error"
        assert warning_call[1]["error_type"] == "validation_error"
        assert warning_call[1]["status_code"] == 422
        assert warning_call[1]["middleware_name"] == "test_exception_handler"
        assert warning_call[1]["platform_context"] == fake_strategy.error_context

    @pytest.mark.anyio
    async def test_server_error_logging(self, middleware, fake_strategy, fake_logger):
        """Test that server errors (5xx) are logged as errors."""

        # Given
        async def handler(*args, **kwargs):
            raise RuntimeError("Internal server error")

        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(handler, event, context=context)

        # Then
        assert result["status_code"] == 500
        assert len(fake_logger.error_calls) == 1
        error_call = fake_logger.error_calls[0]
        assert "Server error occurred" in error_call[0]
        assert error_call[1]["exception_type"] == "RuntimeError"
        assert error_call[1]["status_code"] == 500

    @pytest.mark.anyio
    async def test_stack_trace_inclusion(self, middleware, fake_strategy, fake_logger):
        """Test that stack traces are included when requested."""
        # Given
        middleware_with_trace = ExceptionHandlerMiddleware(
            strategy=fake_strategy,
            include_stack_trace=True,
        )
        # Patch logger
        import src.contexts.shared_kernel.middleware.error_handling.exception_handler as module

        original_get_logger = module.StructlogFactory.get_logger
        module.StructlogFactory.get_logger = MagicMock(return_value=fake_logger)

        try:

            async def handler(*args, **kwargs):
                raise ValueError("Test error")

            event = {"test": "data"}
            context = MagicMock()
            fake_strategy.error_context = {"function_name": "test_function"}

            # When
            result = await middleware_with_trace(handler, event, context=context)

            # Then
            assert result["status_code"] == 422
            assert len(fake_logger.warning_calls) == 1
            warning_call = fake_logger.warning_calls[0]
            assert "stack_trace" in warning_call[1]
            assert "Traceback" in warning_call[1]["stack_trace"]
        finally:
            module.StructlogFactory.get_logger = original_get_logger

    @pytest.mark.anyio
    async def test_internal_details_exposure(self, middleware, fake_strategy):
        """Test that internal details are exposed when configured."""
        # Given
        middleware_with_details = ExceptionHandlerMiddleware(
            strategy=fake_strategy,
            expose_internal_details=True,
        )
        # Patch logger
        import src.contexts.shared_kernel.middleware.error_handling.exception_handler as module

        original_get_logger = module.StructlogFactory.get_logger
        module.StructlogFactory.get_logger = MagicMock(return_value=FakeLogger())

        try:

            async def handler(*args, **kwargs):
                raise ValueError("Test error")

            event = {"test": "data"}
            context = MagicMock()
            fake_strategy.error_context = {"function_name": "test_function"}

            # When
            result = await middleware_with_details(handler, event, context=context)

            # Then
            assert result["detail"] == "ValueError: Test error"
        finally:
            module.StructlogFactory.get_logger = original_get_logger

    @pytest.mark.anyio
    async def test_correlation_id_handling(
        self, middleware, failing_handler, fake_strategy
    ):
        """Test that correlation ID is properly handled."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(failing_handler, event, context=context)

        # Then
        assert "correlation_id" in result
        assert result["correlation_id"] is not None

    @pytest.mark.anyio
    async def test_timestamp_generation(
        self, middleware, failing_handler, fake_strategy
    ):
        """Test that timestamps are generated correctly."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(failing_handler, event, context=context)

        # Then
        assert "timestamp" in result
        # The timestamp should be a datetime object in the result
        timestamp = result["timestamp"]
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo == UTC
        # Should be recent (within last minute)
        now = datetime.now(UTC)
        assert abs((now - timestamp).total_seconds()) < 60

    @pytest.mark.anyio
    async def test_exception_group_with_mixed_errors(
        self, middleware, fake_strategy, fake_logger
    ):
        """Test handling of exception groups with mixed error types."""

        # Given
        async def handler(*args, **kwargs):
            raise ExceptionGroup(
                "Mixed errors",
                [ValueError("Business error"), RuntimeError("System error")],
            )

        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(handler, event, context=context)

        # Then - should prioritize ValueError (business error) over RuntimeError
        assert (
            result["status_code"] == 422
        )  # ValueError is categorized as validation error
        assert result["error_type"] == "validation_error"
        assert result["message"] == "Business error"
        assert len(fake_logger.debug_calls) == 1
        debug_call = fake_logger.debug_calls[0]
        assert "Processing exception group" in debug_call[0]
        assert debug_call[1]["exception_count"] == 2

    @pytest.mark.anyio
    async def test_get_error_context(self, middleware, fake_strategy):
        """Test error context retrieval from request data."""
        # Given
        request_data = {"_error_context": {"test": "context"}}

        # When
        context = middleware.get_error_context(request_data)

        # Then
        assert context == {"test": "context"}

    @pytest.mark.anyio
    async def test_get_error_context_missing(self, middleware):
        """Test error context retrieval when context is missing."""
        # Given
        request_data = {"other": "data"}

        # When
        context = middleware.get_error_context(request_data)

        # Then
        assert context is None


class TestAWSLambdaErrorHandlingStrategy:
    """Test AWS Lambda error handling strategy."""

    def test_extract_error_context_with_event_and_context(self):
        """Test error context extraction from AWS Lambda event and context."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        event = {"test": "data"}
        context = MagicMock()
        context.function_name = "test-function"
        context.request_id = "req-123"
        context.remaining_time_in_millis = 5000

        # When
        error_context = strategy.extract_error_context(event, context)

        # Then
        assert error_context["function_name"] == "test-function"
        assert error_context["request_id"] == "req-123"
        assert error_context["remaining_time_ms"] == 5000

    def test_extract_error_context_missing_attributes(self):
        """Test error context extraction when context attributes are missing."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        event = {"test": "data"}
        context = MagicMock()
        # Remove attributes to simulate missing attributes
        del context.function_name
        del context.request_id
        del context.remaining_time_in_millis

        # When
        error_context = strategy.extract_error_context(event, context)

        # Then
        assert error_context == {}

    def test_get_request_data_from_args(self):
        """Test request data extraction from positional arguments."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        event = {"test": "data"}
        context = MagicMock()

        # When
        extracted_event, extracted_context = strategy.get_request_data(event, context)

        # Then
        assert extracted_event == event
        assert extracted_context == context

    def test_get_request_data_from_kwargs(self):
        """Test request data extraction from keyword arguments."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        event = {"test": "data"}
        context = MagicMock()

        # When
        extracted_event, extracted_context = strategy.get_request_data(
            event=event, context=context
        )

        # Then
        assert extracted_event == event
        assert extracted_context == context

    def test_get_request_data_missing_event_raises_error(self):
        """Test that missing event raises ValueError."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        context = MagicMock()

        # When/Then
        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data(context=context)

    def test_get_request_data_missing_context_raises_error(self):
        """Test that missing context raises ValueError."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        event = {"test": "data"}

        # When/Then
        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data(event=event)

    def test_inject_error_context(self):
        """Test error context injection into request data."""
        # Given
        strategy = AWSLambdaErrorHandlingStrategy()
        request_data = {"test": "data"}
        error_context = {"function_name": "test-function"}

        # When
        strategy.inject_error_context(request_data, error_context)

        # Then
        assert request_data["_error_context"] == error_context


class TestFactoryFunctions:
    """Test factory functions for creating middleware."""

    def test_create_exception_handler_middleware(self, fake_strategy):
        """Test create_exception_handler_middleware factory function."""
        # When
        middleware = create_exception_handler_middleware(
            strategy=fake_strategy,
            name="test_middleware",
            logger_name="test_logger",
            include_stack_trace=True,
            expose_internal_details=True,
            default_error_message="Custom error message",
        )

        # Then
        assert isinstance(middleware, ExceptionHandlerMiddleware)
        assert middleware.name == "test_middleware"
        assert middleware.include_stack_trace is True
        assert middleware.expose_internal_details is True
        assert middleware.default_error_message == "Custom error message"

    def test_aws_lambda_exception_handler_middleware(self):
        """Test aws_lambda_exception_handler_middleware factory function."""
        # When
        middleware = aws_lambda_exception_handler_middleware(
            name="lambda_middleware",
            logger_name="lambda_logger",
            include_stack_trace=True,
            expose_internal_details=False,
            default_error_message="Lambda error occurred",
        )

        # Then
        assert isinstance(middleware, ExceptionHandlerMiddleware)
        assert isinstance(middleware.strategy, AWSLambdaErrorHandlingStrategy)
        assert middleware.name == "lambda_middleware"
        assert middleware.include_stack_trace is True
        assert middleware.expose_internal_details is False
        assert middleware.default_error_message == "Lambda error occurred"


class TestErrorResponseIntegration:
    """Test integration with ErrorResponse models."""

    @pytest.mark.anyio
    async def test_error_response_serialization(
        self, middleware, failing_handler, fake_strategy
    ):
        """Test that error responses are properly serialized."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(failing_handler, event, context=context)

        # Then
        # Verify the result can be used to create an ErrorResponse
        error_response = ErrorResponse(**result)
        assert error_response.status_code == 422
        assert error_response.error_type == ErrorType.VALIDATION_ERROR
        assert error_response.message == "Test validation error"
        assert error_response.correlation_id is not None
        assert isinstance(error_response.timestamp, datetime)

    @pytest.mark.anyio
    async def test_validation_error_details_serialization(
        self, middleware, validation_error_handler, fake_strategy
    ):
        """Test that validation error details are properly serialized."""
        # Given
        event = {"test": "data"}
        context = MagicMock()
        fake_strategy.error_context = {"function_name": "test_function"}

        # When
        result = await middleware(validation_error_handler, event, context=context)

        # Then
        # Verify error details can be deserialized
        error_response = ErrorResponse(**result)
        assert error_response.errors is not None
        assert len(error_response.errors) == 1
        error_detail = error_response.errors[0]
        assert isinstance(error_detail, ErrorDetail)
        assert error_detail.field == "field"
        assert error_detail.code == "string_too_short"
        assert error_detail.message is not None
