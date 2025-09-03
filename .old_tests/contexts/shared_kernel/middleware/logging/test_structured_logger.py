"""
Tests for StructuredLoggingMiddleware.

These tests focus on behavior and outcomes rather than implementation details,
ensuring the middleware correctly logs request/response lifecycle events.
"""

from unittest.mock import patch

import pytest

from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    StructuredLoggingMiddleware,
)
from src.logging.logger import correlation_id_ctx


class TestStructuredLoggingMiddleware:
    """Test StructuredLoggingMiddleware behavior."""

    @pytest.fixture
    def middleware(self):
        """Create a basic logging middleware instance."""
        return StructuredLoggingMiddleware()

    @pytest.fixture
    def mock_handler(self):
        """Create a mock handler that returns a successful response."""

        async def handler(event, context):
            return {"statusCode": 200, "body": "success"}

        return handler

    @pytest.fixture
    def mock_error_handler(self):
        """Create a mock handler that raises an exception."""

        async def handler(event, context):
            raise ValueError("Test error")

        return handler

    @pytest.fixture
    def sample_event(self):
        """Create a sample AWS Lambda event."""
        return {
            "type": "http",
            "httpMethod": "GET",
            "path": "/test",
            "resource": "/test",
            "id": "test-123",
        }

    @pytest.fixture
    def sample_response(self):
        """Create a sample response."""
        return {
            "statusCode": 200,
            "body": "test response",
            "headers": {"Content-Type": "application/json"},
        }

    @pytest.mark.anyio
    async def test_middleware_logs_request_start(
        self, middleware, mock_handler, sample_event
    ):
        """Test that middleware logs when a request starts."""
        with patch.object(middleware.logger, "info") as mock_info:
            mock_context = {"function_name": "test"}
            await middleware(mock_handler, sample_event, mock_context)

            # Verify request start was logged
            mock_info.assert_called()
            call_args = mock_info.call_args_list[0]
            assert "Request started" in call_args[0][0]

    @pytest.mark.anyio
    async def test_middleware_logs_successful_completion(
        self, middleware, mock_handler, sample_event
    ):
        """Test that middleware logs successful request completion."""
        with patch.object(middleware.logger, "info") as mock_info:
            mock_context = {"function_name": "test"}
            await middleware(mock_handler, sample_event, mock_context)

            # Verify successful completion was logged
            mock_info.assert_called()
            call_args = mock_info.call_args_list[1]  # Second call should be completion
            assert "Request completed successfully" in call_args[0][0]

    @pytest.mark.anyio
    async def test_middleware_logs_error_when_handler_fails(
        self, middleware, mock_error_handler, sample_event
    ):
        """Test that middleware logs errors when handler fails."""
        with patch.object(middleware.logger, "error") as mock_error:
            mock_context = {"function_name": "test"}
            with pytest.raises(ValueError):
                await middleware(mock_error_handler, sample_event, mock_context)

            # Verify error was logged
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Request failed" in call_args[0][0]

    @pytest.mark.anyio
    async def test_middleware_captures_correlation_id(
        self, middleware, mock_handler, sample_event
    ):
        """Test that middleware captures and logs correlation ID."""
        test_correlation_id = "test-corr-123"

        with patch.object(middleware.logger, "info") as mock_info:
            # Set correlation ID in context
            correlation_id_ctx.set(test_correlation_id)

            mock_context = {"function_name": "test"}
            await middleware(mock_handler, sample_event, mock_context)

            # Verify correlation ID was captured in logs
            mock_info.assert_called()
            # Check that correlation ID appears in log calls
            for call in mock_info.call_args_list:
                if "Request started" in call[0][0]:
                    assert "correlation_id" in call[1]

    @pytest.mark.anyio
    async def test_middleware_logs_timing_information(
        self, middleware, mock_handler, sample_event
    ):
        """Test that middleware logs execution timing."""
        with patch.object(middleware.logger, "info") as mock_info:
            mock_context = {"function_name": "test"}
            await middleware(mock_handler, sample_event, mock_context)

            # Verify timing was logged in completion
            mock_info.assert_called()
            completion_call = None
            for call in mock_info.call_args_list:
                if "Request completed successfully" in call[0][0]:
                    completion_call = call
                    break

            assert completion_call is not None
            assert "execution_time_ms" in completion_call[1]

    @pytest.mark.anyio
    async def test_middleware_includes_event_summary_when_enabled(self, sample_event):
        """Test that middleware includes event summary when configured."""
        middleware = StructuredLoggingMiddleware(include_event_summary=True)

        with patch.object(middleware.logger, "info") as mock_info:

            async def handler(event, context):
                return {"statusCode": 200}

            mock_context = {"function_name": "test"}
            await middleware(handler, sample_event, mock_context)

            # Verify event summary was included
            mock_info.assert_called()
            start_call = mock_info.call_args_list[0]
            assert "event_summary" in start_call[1]

    @pytest.mark.anyio
    async def test_middleware_includes_response_summary_when_enabled(
        self, sample_event, sample_response
    ):
        """Test that middleware includes response summary when configured."""
        middleware = StructuredLoggingMiddleware(include_response_summary=True)

        with patch.object(middleware.logger, "info") as mock_info:

            async def handler(event, context):
                return sample_response

            mock_context = {"function_name": "test"}
            await middleware(handler, sample_event, mock_context)

            # Verify response summary was included
            mock_info.assert_called()
            completion_call = mock_info.call_args_list[1]
            assert "response_summary" in completion_call[1]

    @pytest.mark.anyio
    async def test_middleware_can_disable_request_logging(self, sample_event):
        """Test that middleware can disable request logging."""
        middleware = StructuredLoggingMiddleware(log_request=False)

        with patch.object(middleware.logger, "info") as mock_info:

            async def handler(event, context):
                return {"statusCode": 200}

            mock_context = {"function_name": "test"}
            await middleware(handler, sample_event, mock_context)

            # Verify only completion was logged (no request start)
            assert mock_info.call_count == 1
            call_args = mock_info.call_args
            assert "Request completed successfully" in call_args[0][0]

    @pytest.mark.anyio
    async def test_middleware_can_disable_response_logging(self, sample_event):
        """Test that middleware can disable response logging."""
        middleware = StructuredLoggingMiddleware(log_response=False)

        with patch.object(middleware.logger, "info") as mock_info:

            async def handler(event, context):
                return {"statusCode": 200}

            mock_context = {"function_name": "test"}
            await middleware(handler, sample_event, mock_context)

            # Verify only request start was logged (no completion)
            assert mock_info.call_count == 1
            call_args = mock_info.call_args
            assert "Request started" in call_args[0][0]

    @pytest.mark.anyio
    async def test_middleware_can_disable_timing_logging(self, sample_event):
        """Test that middleware can disable timing logging."""
        middleware = StructuredLoggingMiddleware(log_timing=False)

        with patch.object(middleware.logger, "info") as mock_info:

            async def handler(event, context):
                return {"statusCode": 200}

            mock_context = {"function_name": "test"}
            await middleware(handler, sample_event, mock_context)

            # Verify timing was not logged
            mock_info.assert_called()
            completion_call = None
            for call in mock_info.call_args_list:
                if "Request completed successfully" in call[0][0]:
                    completion_call = call
                    break

            assert completion_call is not None
            assert "execution_time_ms" not in completion_call[1]

    @pytest.mark.anyio
    async def test_middleware_can_disable_correlation_id_logging(self, sample_event):
        """Test that middleware can disable correlation ID logging."""
        middleware = StructuredLoggingMiddleware(log_correlation_id=False)

        with patch.object(middleware.logger, "info") as mock_info:

            async def handler(event, context):
                return {"statusCode": 200}

            mock_context = {"function_name": "test"}
            await middleware(handler, sample_event, mock_context)

            # Verify correlation ID was not logged
            mock_info.assert_called()
            for call in mock_info.call_args_list:
                # Check that correlation_id is not in the log data
                log_data = call[1]
                if "correlation_id" in log_data:
                    assert log_data["correlation_id"] is None

    @pytest.mark.anyio
    async def test_middleware_preserves_handler_response(
        self, middleware, sample_event
    ):
        """Test that middleware preserves the original handler response."""
        expected_response = {"statusCode": 200, "body": "test"}

        async def handler(event, context):
            return expected_response

        mock_context = {"function_name": "test"}
        response = await middleware(handler, sample_event, mock_context)

        assert response == expected_response

    @pytest.mark.anyio
    async def test_middleware_propagates_exceptions(self, middleware, sample_event):
        """Test that middleware propagates exceptions from handler."""
        expected_error = ValueError("Test error")

        async def handler(event, context):
            raise expected_error

        mock_context = {"function_name": "test"}
        with pytest.raises(ValueError, match="Test error"):
            await middleware(handler, sample_event, mock_context)

    def test_middleware_initialization_with_custom_name(self):
        """Test that middleware can be initialized with a custom name."""
        custom_name = "CustomLoggingMiddleware"
        middleware = StructuredLoggingMiddleware(name=custom_name)

        assert middleware.name == custom_name

    def test_middleware_initialization_with_custom_logger_name(self):
        """Test that middleware can be initialized with a custom logger name."""
        custom_logger_name = "custom.logger"
        middleware = StructuredLoggingMiddleware(logger_name=custom_logger_name)

        # Verify the logger was created with the custom name
        assert middleware.logger.name == custom_logger_name
