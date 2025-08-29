"""
Unit tests for error middleware functionality.

Tests cover:
- Exception handling and categorization
- Error response generation
- Correlation ID integration
- Structured logging validation
- Configuration options for different environments
"""

import json
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field, ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.responses.error_response import (
    ErrorType,
)
from src.contexts.shared_kernel.middleware.error_middleware import (
    ErrorMiddleware,
    create_error_middleware,
    development_error_middleware,
    legacy_compatible_error_middleware,
    production_error_middleware,
)

pytestmark = pytest.mark.anyio


class MockModel(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., gt=0)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")


class TestErrorMiddleware:
    """Test suite for ErrorMiddleware class."""

    @pytest.fixture
    def basic_middleware(self):
        """Create basic error middleware for testing."""
        return ErrorMiddleware(
            logger_name="test_error_handler",
            include_stack_trace=False,
            expose_internal_details=False,
        )

    @pytest.fixture
    def development_middleware(self):
        """Create development error middleware with full details."""
        return ErrorMiddleware(
            logger_name="test_dev_handler",
            include_stack_trace=True,
            expose_internal_details=True,
        )

    @pytest.fixture
    def mock_event(self):
        """Create mock AWS Lambda event."""
        return {
            "httpMethod": "POST",
            "path": "/api/test",
            "headers": {"Content-Type": "application/json"},
            "body": '{"test": "data"}',
            "requestContext": {"authorizer": {"user_id": "test-user-123"}},
        }

    async def test_successful_handler_passthrough(self, basic_middleware, mock_event):
        """Test that successful handlers pass through without modification."""

        async def successful_handler(event):
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"result": "success"}),
            }

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            response = await basic_middleware(successful_handler, mock_event)

            assert response["statusCode"] == 200
            assert "result" in json.loads(response["body"])

    async def test_exception_handling_basic(self, basic_middleware, mock_event):
        """Test basic exception handling and error response generation."""

        async def failing_handler(event):
            raise ValueError("Test validation error")

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            response = await basic_middleware(failing_handler, mock_event)

            assert response["statusCode"] == 422  # ValueError maps to validation error
            assert "application/json" in response["headers"]["Content-Type"]

            error_body = json.loads(response["body"])
            assert error_body["error_type"] == "validation_error"
            assert error_body["correlation_id"] == "test-correlation-123"
            assert (
                "occurred while processing" in error_body["message"]
            )  # Default safe message

    async def test_exception_categorization_mapping(self, basic_middleware, mock_event):
        """Test that different exception types are correctly categorized."""
        test_cases = [
            (ValueError("test"), ErrorType.VALIDATION_ERROR, 422),
            (KeyError("missing"), ErrorType.NOT_FOUND_ERROR, 404),
            (PermissionError("denied"), ErrorType.AUTHORIZATION_ERROR, 403),
            (TimeoutError("timeout"), ErrorType.TIMEOUT_ERROR, 408),
            (ConnectionError("connection"), ErrorType.TIMEOUT_ERROR, 408),
        ]

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            for exception, expected_type, expected_status in test_cases:

                async def failing_handler(event):
                    raise exception

                response = await basic_middleware(failing_handler, mock_event)
                error_body = json.loads(response["body"])

                assert response["statusCode"] == expected_status
                assert error_body["error_type"] == expected_type.value

    async def test_exception_categorization_by_message(
        self, basic_middleware, mock_event
    ):
        """Test exception categorization based on error message patterns."""
        test_cases = [
            (Exception("Entity not found in database"), ErrorType.NOT_FOUND_ERROR, 404),
            (Exception("User not authenticated"), ErrorType.AUTHENTICATION_ERROR, 401),
            (Exception("Access denied for user"), ErrorType.AUTHORIZATION_ERROR, 403),
            (Exception("Record already exists"), ErrorType.CONFLICT_ERROR, 409),
            (Exception("Request timed out"), ErrorType.TIMEOUT_ERROR, 408),
            (Exception("Invalid format provided"), ErrorType.VALIDATION_ERROR, 422),
        ]

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            for exception, expected_type, expected_status in test_cases:

                async def failing_handler(event):
                    raise exception

                response = await basic_middleware(failing_handler, mock_event)
                error_body = json.loads(response["body"])

                assert response["statusCode"] == expected_status
                assert error_body["error_type"] == expected_type.value

    async def test_pydantic_validation_error_handling(
        self, basic_middleware, mock_event
    ):
        """Test special handling of Pydantic ValidationError with real validation errors."""

        async def failing_handler(event):
            # Create a real ValidationError by validating invalid data
            try:
                MockModel.model_validate(
                    {
                        "name": "",  # Too short (min_length=1)
                        "age": -5,  # Too small (gt=0)
                        "email": "invalid-email",  # Invalid format
                    }
                )
            except ValidationError as e:
                raise e

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            response = await basic_middleware(failing_handler, mock_event)
            error_body = json.loads(response["body"])

            assert response["statusCode"] == 422
            assert error_body["error_type"] == "validation_error"
            assert error_body["message"] == "Validation failed"
            assert "errors" in error_body
            assert (
                len(error_body["errors"]) >= 3
            )  # Should have validation errors for all fields

            # Verify error structure contains expected fields
            error_fields = [error["field"] for error in error_body["errors"]]
            assert "name" in error_fields
            assert "age" in error_fields
            assert "email" in error_fields

    async def test_development_error_exposure(self, development_middleware, mock_event):
        """Test that development middleware exposes internal error details."""

        async def failing_handler(event):
            raise RuntimeError("Internal system error with sensitive data")

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            response = await development_middleware(failing_handler, mock_event)
            error_body = json.loads(response["body"])

            assert "Internal system error with sensitive data" in error_body["message"]
            assert "Internal system error with sensitive data" in error_body["detail"]
            assert error_body["context"] is not None
            assert "stack_trace" in error_body["context"]

    async def test_production_error_safety(self, basic_middleware, mock_event):
        """Test that production middleware hides internal error details."""

        async def failing_handler(event):
            raise RuntimeError("Internal system error with sensitive data")

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            response = await basic_middleware(failing_handler, mock_event)
            error_body = json.loads(response["body"])

            assert (
                "Internal system error with sensitive data" not in error_body["message"]
            )
            assert (
                error_body["message"]
                == "An error occurred while processing your request"
            )
            assert error_body["detail"] == "An internal server error occurred"
            assert error_body.get("context") is None

    async def test_error_logging_captures_context(self, basic_middleware, mock_event):
        """Test that errors are logged with proper context information."""

        async def failing_handler(event):
            raise ValueError("Test error for logging")

        with (
            patch(
                "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
            ) as mock_ctx,
            patch.object(basic_middleware, "structured_logger") as mock_logger,
        ):

            mock_ctx.get.return_value = "test-correlation-123"

            await basic_middleware(failing_handler, mock_event)

            # Verify that logging was called (behavior)
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args

            # Verify the logged context contains expected information
            assert "Client error occurred" in call_args[0][0]
            logged_context = call_args[1]
            assert logged_context["correlation_id"] == "test-correlation-123"
            assert logged_context["method"] == "POST"
            assert logged_context["path"] == "/api/test"
            assert logged_context["error_type"] == "validation_error"
            assert logged_context["status_code"] == 422
            assert logged_context["user_id"] == "test-user-123"

    async def test_server_error_logging_severity(self, basic_middleware, mock_event):
        """Test that server errors are logged with appropriate severity."""

        async def failing_handler(event):
            raise Exception("Internal server failure")

        with (
            patch(
                "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
            ) as mock_ctx,
            patch.object(basic_middleware, "structured_logger") as mock_logger,
        ):

            mock_ctx.get.return_value = "test-correlation-123"

            await basic_middleware(failing_handler, mock_event)

            # Verify error was logged with error level for 5xx status
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args

            assert "Internal server error occurred" in call_args[0][0]
            assert call_args[1]["status_code"] == 500
            assert "stack_trace" in call_args[1]

    async def test_cors_headers_in_error_response(self, basic_middleware, mock_event):
        """Test that error responses include proper CORS headers."""

        async def failing_handler(event):
            raise ValueError("Test validation error")

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = "test-correlation-123"

            response = await basic_middleware(failing_handler, mock_event)

            headers = response["headers"]
            assert headers["Access-Control-Allow-Origin"] == "*"
            assert "Content-Type" in headers["Access-Control-Allow-Headers"]
            assert (
                "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT"
                in headers["Access-Control-Allow-Methods"]
            )

    async def test_error_context_manager_behavior(self, basic_middleware):
        """Test the error context manager functionality with real exceptions."""
        with (
            patch(
                "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
            ) as mock_ctx,
            patch.object(basic_middleware, "structured_logger") as mock_logger,
        ):

            mock_ctx.get.return_value = "test-correlation-123"

            # Test that exceptions are properly re-raised
            with pytest.raises(ValueError, match="Test error in context"):
                async with basic_middleware.error_context("test_operation"):
                    raise ValueError("Test error in context")

            # Verify error was logged with operation context
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args

            assert "Error in test_operation" in call_args[0][0]
            logged_context = call_args[1]
            assert logged_context["operation"] == "test_operation"
            assert logged_context["correlation_id"] == "test-correlation-123"
            assert logged_context["exception_type"] == "ValueError"

    async def test_correlation_id_fallback_behavior(self, basic_middleware, mock_event):
        """Test behavior when correlation ID is not available."""

        async def failing_handler(event):
            raise ValueError("Test validation error")

        with patch(
            "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
        ) as mock_ctx:
            mock_ctx.get.return_value = None  # No correlation ID available

            response = await basic_middleware(failing_handler, mock_event)
            error_body = json.loads(response["body"])

            # Should default to "unknown" when no correlation ID
            assert error_body["correlation_id"] == "unknown"

    async def test_missing_user_context_handling(self, basic_middleware):
        """Test handling when user context is not available."""
        event_no_user = {
            "httpMethod": "GET",
            "path": "/api/test",
            "requestContext": {},  # No authorizer
        }

        async def failing_handler(event):
            raise ValueError("Test validation error")

        with (
            patch(
                "src.contexts.shared_kernel.middleware.error_middleware.correlation_id_ctx"
            ) as mock_ctx,
            patch.object(basic_middleware, "structured_logger") as mock_logger,
        ):

            mock_ctx.get.return_value = "test-correlation-123"

            await basic_middleware(failing_handler, event_no_user)

            # Verify that user_id is not included when not available
            call_args = mock_logger.warning.call_args
            logged_context = call_args[1]
            assert "user_id" not in logged_context


class TestErrorMiddlewareFactories:
    """Test suite for error middleware factory functions."""

    def test_create_error_middleware_default(self):
        """Test default error middleware creation."""
        middleware = create_error_middleware()

        assert not middleware.include_stack_trace
        assert not middleware.expose_internal_details

    def test_create_error_middleware_custom(self):
        """Test custom error middleware creation."""
        middleware = create_error_middleware(
            include_stack_trace=True, expose_internal_details=True
        )

        assert middleware.include_stack_trace
        assert middleware.expose_internal_details

    def test_development_error_middleware_factory(self):
        """Test development environment factory."""
        middleware = development_error_middleware()

        assert middleware.include_stack_trace
        assert middleware.expose_internal_details
        assert "Development" in middleware.default_error_message

    def test_production_error_middleware_factory(self):
        """Test production environment factory."""
        middleware = production_error_middleware()

        assert not middleware.include_stack_trace
        assert not middleware.expose_internal_details
        assert "occurred while processing" in middleware.default_error_message

    def test_legacy_compatible_error_middleware_factory(self):
        """Test legacy compatibility factory."""
        middleware = legacy_compatible_error_middleware()

        assert not middleware.include_stack_trace
        assert middleware.expose_internal_details  # For backward compatibility
        assert middleware.default_error_message == "Request failed"
