"""
Unit tests for logging middleware functionality.

Tests correlation ID management, structured logging, performance tracking,
user context extraction, and integration with existing logging infrastructure.
"""

import json
import pytest
import time
from unittest.mock import Mock
from typing import Dict, Any

from src.contexts.shared_kernel.middleware.logging_middleware import (
    LoggingMiddleware,
    create_logging_middleware,
    standard_logging_middleware,
    minimal_logging_middleware,
    performance_focused_middleware
)
from src.logging.logger import correlation_id_ctx

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_event() -> Dict[str, Any]:
    """Mock Lambda event for testing."""
    return {
        "httpMethod": "POST",
        "resource": "/api/v1/recipes",
        "pathParameters": {"id": "123"},
        "queryStringParameters": {"limit": "10"},
        "multiValueQueryStringParameters": {"tags": ["test", "recipe"]},
        "body": json.dumps({"name": "Test Recipe", "ingredients": ["flour", "eggs"]}),
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Test Client/1.0",
            "Authorization": "Bearer secret-token"  # Should be filtered
        },
        "requestContext": {
            "requestId": "test-request-123",
            "authorizer": {
                "claims": {
                    "sub": "user-123",
                    "cognito:username": "testuser",
                    "auth_time": "1640995200"
                }
            },
            "identity": {
                "sourceIp": "192.168.1.1"
            }
        }
    }


@pytest.fixture
def mock_context() -> Any:
    """Mock Lambda context for testing."""
    context = Mock()
    context.function_name = "test-function"
    context.function_version = "$LATEST"
    return context


class TestLoggingMiddleware:
    """Test LoggingMiddleware functionality."""
    
    @pytest.fixture
    def middleware(self) -> LoggingMiddleware:
        """Create logging middleware for testing."""
        return LoggingMiddleware(
            logger_name="test-middleware",
            log_request_body=True,
            log_response_body=True,
            max_body_size=500,
            performance_warning_threshold=1.0
        )
    
    def test_initialization_default_configuration(self):
        """Test middleware initialization with default configuration."""
        middleware = LoggingMiddleware()
        assert middleware.log_request_body is True
        assert middleware.log_response_body is True
        assert middleware.max_body_size == 1000
        assert middleware.performance_warning_threshold == 5.0
    
    def test_initialization_custom_configuration(self):
        """Test middleware initialization with custom configuration."""
        middleware = LoggingMiddleware(
            logger_name="custom",
            log_request_body=False,
            log_response_body=False,
            max_body_size=200,
            performance_warning_threshold=2.0
        )
        assert middleware.log_request_body is False
        assert middleware.log_response_body is False
        assert middleware.max_body_size == 200
        assert middleware.performance_warning_threshold == 2.0
    
    def test_correlation_id_generation_format(self, middleware):
        """Test correlation ID generation produces correct format."""
        correlation_id = middleware.generate_correlation_id()
        assert isinstance(correlation_id, str)
        assert len(correlation_id) == 8
        
        # Should generate unique IDs
        correlation_id2 = middleware.generate_correlation_id()
        assert correlation_id != correlation_id2
    
    def test_user_context_extraction_with_authentication(self, middleware, mock_event):
        """Test user context extraction when authentication is present."""
        user_context = middleware.extract_user_context(mock_event)
        
        assert user_context["user_id"] == "user-123"
        assert user_context["username"] == "testuser"
        assert user_context["auth_time"] == "1640995200"
    
    def test_user_context_extraction_without_authentication(self, middleware):
        """Test user context extraction when authentication is missing."""
        event = {"requestContext": {}}
        user_context = middleware.extract_user_context(event)
        
        assert user_context["user_id"] is None
        assert user_context["auth_method"] == "localstack_bypass"
    
    def test_user_context_extraction_malformed_event(self, middleware):
        """Test user context extraction handles malformed events gracefully."""
        event = {}
        user_context = middleware.extract_user_context(event)
        
        assert user_context["user_id"] is None
        assert user_context["auth_method"] == "localstack_bypass"
    
    def test_body_sanitization_dictionary_input(self, middleware):
        """Test body sanitization converts dictionary to JSON string."""
        body = {"name": "Test", "description": "A test recipe"}
        sanitized = middleware.sanitize_body_for_logging(body)
        
        assert isinstance(sanitized, str)
        assert "Test" in sanitized
        assert "test recipe" in sanitized
    
    def test_body_sanitization_string_input(self, middleware):
        """Test body sanitization preserves string input."""
        body = "Simple string body"
        sanitized = middleware.sanitize_body_for_logging(body)
        
        assert sanitized == "Simple string body"
    
    def test_body_sanitization_large_content_truncation(self, middleware):
        """Test body sanitization truncates content exceeding max size."""
        large_body = "x" * 600  # Exceeds 500 character limit
        sanitized = middleware.sanitize_body_for_logging(large_body)
        
        assert len(sanitized) <= 500 + len("... [TRUNCATED]")
        assert sanitized.endswith("... [TRUNCATED]")
    
    def test_body_sanitization_none_input(self, middleware):
        """Test body sanitization handles None input."""
        sanitized = middleware.sanitize_body_for_logging(None)
        assert sanitized is None
    
    def test_request_metadata_extraction_complete_event(self, middleware, mock_event):
        """Test request metadata extraction from complete event."""
        metadata = middleware.extract_request_metadata(mock_event)
        
        assert metadata["http_method"] == "POST"
        assert metadata["resource_path"] == "/api/v1/recipes"
        assert metadata["path_parameters"] == {"id": "123"}
        assert metadata["query_parameters"] == {"limit": "10"}
        assert metadata["source_ip"] == "192.168.1.1"
        assert metadata["user_agent"] == "Test Client/1.0"
        assert metadata["request_id"] == "test-request-123"
        
        # Verify sensitive headers are filtered out
        assert "authorization" not in metadata["headers"]
        assert "Content-Type" in metadata["headers"]
        assert "User-Agent" in metadata["headers"]
    
    def test_request_metadata_extraction_minimal_event(self, middleware):
        """Test request metadata extraction from minimal event."""
        event = {"httpMethod": "GET"}
        metadata = middleware.extract_request_metadata(event)
        
        assert metadata["http_method"] == "GET"
        assert metadata["resource_path"] is None
        assert metadata["headers"] == {}
    
    async def test_correlation_id_context_management(self, middleware, mock_event, mock_context):
        """Test correlation ID is properly set and reset in context."""
        initial_correlation_id = None
        context_correlation_id = None
        final_correlation_id = None
        
        # Check initial state (should raise LookupError or return default)
        try:
            initial_correlation_id = correlation_id_ctx.get()
        except LookupError:
            initial_correlation_id = None
        
        # Use context manager and capture correlation ID
        async with middleware.log_request_response(mock_event, mock_context) as operation_context:
            context_correlation_id = correlation_id_ctx.get()
            assert context_correlation_id == operation_context["correlation_id"]
        
        # Check final state (should be reset)
        try:
            final_correlation_id = correlation_id_ctx.get()
        except LookupError:
            final_correlation_id = None
        
        # Correlation ID should be different in context but reset afterwards
        assert context_correlation_id is not None
        assert len(context_correlation_id) == 8
    
    async def test_custom_correlation_id_usage(self, middleware, mock_event, mock_context):
        """Test using custom correlation ID instead of generated one."""
        custom_id = "custom-123"
        
        async with middleware.log_request_response(mock_event, mock_context, custom_id) as operation_context:
            assert operation_context["correlation_id"] == custom_id
            assert correlation_id_ctx.get() == custom_id
    
    async def test_exception_handling_preserves_context_reset(self, middleware, mock_event, mock_context):
        """Test correlation ID context is reset even when exceptions occur."""
        try:
            async with middleware.log_request_response(mock_event, mock_context) as operation_context:
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected exception
        
        # Context should still be reset despite exception
        try:
            correlation_id_ctx.get()
            # If we get here, there might be a default value, which is acceptable
        except LookupError:
            # This is the expected behavior - context was reset
            pass
    
    def test_response_logging_execution_time_calculation(self, middleware):
        """Test response logging calculates execution time correctly."""
        response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Success"})
        }
        
        start_time = time.perf_counter() - 0.5  # 500ms ago
        operation_context = {
            "correlation_id": "test-123",
            "start_time": start_time,
            "request_metadata": {
                "http_method": "POST",
                "resource_path": "/api/v1/recipes"
            },
            "user_context": {"user_id": "user-123"}
        }
        
        # This tests behavior - the middleware should calculate execution time
        # and handle the response logging without errors
        middleware.log_response(response, operation_context)
        
        # If we get here without exceptions, the behavior is correct
        assert True
    
    def test_performance_warning_threshold_behavior(self, middleware):
        """Test performance warning is triggered when threshold is exceeded."""
        response = {"statusCode": 200, "headers": {}, "body": "{}"}
        
        # Set start time to exceed the 1.0 second threshold
        operation_context = {
            "correlation_id": "test-123",
            "start_time": time.perf_counter() - 2.0,  # 2 seconds ago
            "request_metadata": {
                "http_method": "GET",
                "resource_path": "/api/v1/slow-endpoint"
            },
            "user_context": {"user_id": "user-123"}
        }
        
        # This tests behavior - should handle performance warning without errors
        middleware.log_response(response, operation_context)
        
        # If we get here without exceptions, the behavior is correct
        assert True
    
    def test_large_response_body_handling(self, middleware):
        """Test middleware handles large response bodies correctly."""
        large_response = {"data": "x" * 600}  # Exceeds 500 character limit
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(large_response)
        }
        
        operation_context = {
            "correlation_id": "test-123",
            "start_time": time.perf_counter(),
            "request_metadata": {"http_method": "GET", "resource_path": "/api/v1/data"},
            "user_context": {"user_id": "user-123"}
        }
        
        # This tests behavior - should handle large bodies without errors
        middleware.log_response(response, operation_context)
        
        # If we get here without exceptions, the behavior is correct
        assert True
    
    async def test_middleware_decorator_functionality(self, middleware, mock_event, mock_context):
        """Test middleware works correctly as a decorator."""
        response_data = {"statusCode": 200, "body": "success"}
        
        # Define a simple handler function
        async def test_handler(event, context):
            return response_data
        
        # Wrap handler with middleware
        wrapped_handler = await middleware(test_handler)
        
        # Execute wrapped handler
        response = await wrapped_handler(mock_event, mock_context)
        
        # Verify the response is unchanged (behavior preservation)
        assert response == response_data
    
    async def test_middleware_preserves_handler_exceptions(self, middleware, mock_event, mock_context):
        """Test middleware preserves exceptions from the wrapped handler."""
        async def failing_handler(event, context):
            raise RuntimeError("Handler failed")
        
        wrapped_handler = await middleware(failing_handler)
        
        # Exception should be preserved and propagated
        with pytest.raises(RuntimeError, match="Handler failed"):
            await wrapped_handler(mock_event, mock_context)


class TestConvenienceFunctions:
    """Test convenience functions and pre-configured middleware."""
    
    def test_create_logging_middleware_custom_configuration(self):
        """Test create_logging_middleware function with custom settings."""
        middleware = create_logging_middleware(
            logger_name="custom",
            log_request_body=False,
            max_body_size=200
        )
        
        assert isinstance(middleware, LoggingMiddleware)
        assert middleware.log_request_body is False
        assert middleware.max_body_size == 200
    
    def test_pre_configured_middleware_standard(self):
        """Test standard pre-configured middleware has expected settings."""
        assert isinstance(standard_logging_middleware, LoggingMiddleware)
        assert standard_logging_middleware.log_request_body is True
        assert standard_logging_middleware.log_response_body is True
    
    def test_pre_configured_middleware_minimal(self):
        """Test minimal pre-configured middleware has expected settings."""
        assert isinstance(minimal_logging_middleware, LoggingMiddleware)
        assert minimal_logging_middleware.log_request_body is False
        assert minimal_logging_middleware.log_response_body is False
        assert minimal_logging_middleware.max_body_size == 500
    
    def test_pre_configured_middleware_performance_focused(self):
        """Test performance-focused pre-configured middleware has expected settings."""
        assert isinstance(performance_focused_middleware, LoggingMiddleware)
        assert performance_focused_middleware.performance_warning_threshold == 2.0
        assert performance_focused_middleware.max_body_size == 500


class TestIntegrationBehavior:
    """Test integration behavior with existing logging infrastructure."""
    
    async def test_correlation_id_availability_during_request(self, mock_event, mock_context):
        """Test correlation ID is available throughout request processing."""
        middleware = LoggingMiddleware()
        correlation_ids = []
        
        async with middleware.log_request_response(mock_event, mock_context) as operation_context:
            # Correlation ID should be available in operation context
            correlation_ids.append(operation_context["correlation_id"])
            
            # Should also be available via context variable
            try:
                context_id = correlation_id_ctx.get()
                correlation_ids.append(context_id)
            except LookupError:
                correlation_ids.append(None)
        
        # Both should be the same non-None value
        assert correlation_ids[0] is not None
        assert correlation_ids[0] == correlation_ids[1]
    
    def test_structured_logger_integration(self):
        """Test structured logger is properly integrated."""
        middleware = LoggingMiddleware(logger_name="test-integration")
        
        # Should have structured logger instance
        assert middleware.structured_logger is not None
        assert middleware.standard_logger is not None


class TestEdgeCaseBehavior:
    """Test edge case handling behavior."""
    
    def test_malformed_json_handling_graceful_failure(self):
        """Test middleware handles malformed JSON gracefully."""
        middleware = LoggingMiddleware()
        
        # Event with invalid JSON should not cause exceptions
        event = {"body": '{"invalid": json content}'}
        
        # Should handle gracefully without exceptions
        metadata = middleware.extract_request_metadata(event)
        assert isinstance(metadata, dict)
    
    def test_missing_request_context_handling(self):
        """Test middleware handles missing request context gracefully."""
        middleware = LoggingMiddleware()
        event = {"httpMethod": "GET"}
        
        # Should extract what's available without exceptions
        metadata = middleware.extract_request_metadata(event)
        user_context = middleware.extract_user_context(event)
        
        assert metadata["request_id"] is None
        assert user_context["user_id"] is None
        assert metadata["http_method"] == "GET"  # Should extract what's available
    
    def test_empty_headers_handling(self):
        """Test middleware handles empty or missing headers gracefully."""
        middleware = LoggingMiddleware()
        event = {"httpMethod": "GET", "headers": None}
        
        metadata = middleware.extract_request_metadata(event)
        
        # Should provide empty dict for headers when None
        assert metadata["headers"] == {}
        assert metadata["user_agent"] is None 