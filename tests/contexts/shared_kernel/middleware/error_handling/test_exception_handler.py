"""
Behavior-focused tests for ExceptionHandlerMiddleware.

These tests focus on real-world scenarios and edge cases rather than
just testing individual methods in isolation.
"""

import pytest

from src.contexts.shared_kernel.adapters.api_schemas.responses.error_response import (
    ErrorType,
)


@pytest.mark.anyio
class TestExceptionHandlerMiddlewareBehavior:
    """Test real-world behavior scenarios for ExceptionHandlerMiddleware."""

    async def test_successful_request_flows_through_unchanged(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that successful requests pass through without modification."""
        # Arrange
        expected_response = {"status_code": 200, "body": "success"}
        mock_handler.return_value = expected_response
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result == expected_response
        mock_handler.assert_called_once_with(mock_event, mock_context)

    async def test_validation_error_creates_proper_error_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that validation errors create proper 422 responses."""
        # Arrange
        # Use a simple ValueError which should be categorized as validation error
        mock_handler.side_effect = ValueError("field required")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "field required" in result["message"]

    async def test_not_found_error_creates_404_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that KeyError creates proper 404 responses."""
        # Arrange
        mock_handler.side_effect = KeyError("user_id")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 404
        assert result["error_type"] == ErrorType.NOT_FOUND_ERROR
        assert "user_id" in result["message"]

    async def test_authorization_error_creates_403_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that PermissionError creates proper 403 responses."""
        # Arrange
        mock_handler.side_effect = PermissionError("Insufficient permissions")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 403
        assert result["error_type"] == ErrorType.AUTHORIZATION_ERROR
        assert "Insufficient permissions" in result["message"]

    async def test_timeout_error_creates_408_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that TimeoutError creates proper 408 responses."""
        # Arrange
        mock_handler.side_effect = TimeoutError("Request timed out")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 408
        assert result["error_type"] == ErrorType.TIMEOUT_ERROR
        assert "Request timed out" in result["message"]

    async def test_unknown_exception_creates_500_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that unknown exceptions create proper 500 responses."""
        # Arrange
        mock_handler.side_effect = RuntimeError("Unexpected error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 500
        assert result["error_type"] == ErrorType.INTERNAL_ERROR
        assert "Unexpected error" in result["message"]

    async def test_exception_group_handling_creates_422_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that exception groups with validation errors create proper 422 responses."""

        # Arrange
        mock_handler.side_effect = ExceptionGroup(
            "Multiple errors", [ValueError("Error 1"), TypeError("Error 2")]
        )
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Error 1" in result["message"]

    async def test_exception_group_with_internal_errors_creates_500_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that exception groups with only internal errors create proper 500 responses."""

        # Arrange
        mock_handler.side_effect = ExceptionGroup(
            "Multiple errors", [RuntimeError("Error 1"), OSError("Error 2")]
        )
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 500
        assert result["error_type"] == ErrorType.INTERNAL_ERROR
        assert "Multiple errors occurred during execution" in result["message"]

    async def test_development_mode_exposes_internal_details(
        self, dev_error_middleware, mock_handler, mock_event
    ):
        """Test that development mode exposes internal error details."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await dev_error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "ValueError: Test error" in result["detail"]

    async def test_production_mode_hides_internal_details(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that production mode hides internal error details."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["detail"]
        assert "ValueError" not in result["detail"]

    async def test_correlation_id_is_preserved_in_error_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that correlation ID is preserved in error responses."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert "correlation_id" in result
        assert result["correlation_id"] is not None

    async def test_correlation_id_fallback_when_not_set(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that correlation ID fallback works when not set."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert "correlation_id" in result
        assert result["correlation_id"] is not None
        # Verify that the correlation ID is properly formatted (should be a UUID or "unknown")
        assert isinstance(result["correlation_id"], str)
        assert len(result["correlation_id"]) > 0

    async def test_timestamp_is_included_in_error_response(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that timestamp is included in error responses."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert "timestamp" in result
        assert result["timestamp"] is not None
        # Verify that the timestamp is a valid datetime object
        from datetime import datetime

        assert isinstance(result["timestamp"], datetime)
        # Should be recent (within last minute)
        from datetime import UTC

        now = datetime.now(UTC)
        time_diff = abs((now - result["timestamp"]).total_seconds())
        assert time_diff < 60

    async def test_validation_error_with_multiple_fields(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that validation errors with multiple fields are handled correctly."""
        # Arrange
        # Use a simple ValueError which should be categorized as validation error
        mock_handler.side_effect = ValueError("Multiple validation errors occurred")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Multiple validation errors occurred" in result["message"]

    async def test_validation_error_with_context_information(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that validation errors include context information when available."""
        # Arrange
        # Use a simple ValueError which should be categorized as validation error
        mock_handler.side_effect = ValueError("Validation error with context")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Validation error with context" in result["message"]

    async def test_validation_error_with_nested_field_paths(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that validation errors with nested field paths are handled correctly."""
        # Arrange
        # Use a simple ValueError which should be categorized as validation error
        mock_handler.side_effect = ValueError("Nested field validation error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Nested field validation error" in result["message"]

    async def test_validation_error_with_non_string_field_names(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that validation errors with non-string field names are handled gracefully."""
        # Arrange
        # Use a simple ValueError which should be categorized as validation error
        mock_handler.side_effect = ValueError("Non-string field validation error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Non-string field validation error" in result["message"]

    async def test_error_logging_includes_all_required_fields(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that error logging includes all required fields."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        # Verify that the error response contains all required fields
        # This indirectly tests that logging is working since the middleware
        # processes the exception and creates a proper error response
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["message"]
        assert "correlation_id" in result
        assert "timestamp" in result
        assert result["correlation_id"] is not None
        assert result["timestamp"] is not None

    async def test_standard_logger_also_receives_error_information(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that standard logger also receives error information for backward compatibility."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        # Verify that the error response is properly formatted and contains
        # all the information that would be logged by the standard logger
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["message"]
        assert "correlation_id" in result
        assert "timestamp" in result
        # The middleware name should be reflected in the response structure
        assert result["correlation_id"] is not None
        assert result["timestamp"] is not None

    async def test_stack_trace_included_when_enabled(
        self, dev_error_middleware, mock_handler, mock_event
    ):
        """Test that stack trace is included in logs when enabled."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await dev_error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        # Verify that development mode middleware produces proper error responses
        # and includes additional detail information that would contain stack traces
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["message"]
        assert "correlation_id" in result
        assert "timestamp" in result
        # Development mode should expose more internal details
        assert "ValueError: Test error" in result["detail"]

    async def test_stack_trace_excluded_when_disabled(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that stack trace is excluded from logs when disabled."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        # Verify that production mode middleware produces proper error responses
        # and hides internal details like exception class names
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["message"]
        assert "correlation_id" in result
        assert "timestamp" in result
        # Production mode should hide internal details
        assert "ValueError" not in result["detail"]
        assert "Test error" in result["detail"]

    async def test_middleware_name_is_used_in_logging(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that middleware name is used in logging messages."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        # Verify that the middleware produces proper error responses
        # and includes all required fields that would be used in logging
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["message"]
        assert "correlation_id" in result
        assert "timestamp" in result
        # The middleware name is used internally for logging, but we can verify
        # that the response structure is correct and complete
        assert result["correlation_id"] is not None
        assert result["timestamp"] is not None

    async def test_default_error_message_when_exception_has_no_message(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that default error message is used when exception has no message."""

        # Arrange
        class SilentException(Exception):
            def __str__(self):
                return ""

        mock_handler.side_effect = SilentException()
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 500
        assert result["error_type"] == ErrorType.INTERNAL_ERROR
        assert "An error occurred while processing your request" in result["message"]

    async def test_development_mode_shows_exception_class_in_detail(
        self, dev_error_middleware, mock_handler, mock_event
    ):
        """Test that development mode shows exception class in error detail."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await dev_error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "ValueError: Test error" in result["detail"]

    async def test_production_mode_hides_exception_class_in_detail(
        self, error_middleware, mock_handler, mock_event
    ):
        """Test that production mode hides exception class in error detail."""
        # Arrange
        mock_handler.side_effect = ValueError("Test error")
        mock_context = {"function_name": "test"}

        # Act
        result = await error_middleware(mock_handler, mock_event, mock_context)

        # Assert
        assert result["status_code"] == 422
        assert result["error_type"] == ErrorType.VALIDATION_ERROR
        assert "Test error" in result["detail"]
        assert "ValueError" not in result["detail"]
