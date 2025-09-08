"""Security tests for exception handler middleware.

Tests security aspects of the exception handler middleware including:
- Security headers in error responses
- Prevention of information leakage in error responses
- Input validation and sanitization
- Error response structure security

Focuses on ensuring that error responses don't expose sensitive information
and include appropriate security headers for HTTP security.
"""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest import fixture
from src.contexts.shared_kernel.middleware.error_handling.error_response import (
    ErrorType,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    AWSLambdaErrorHandlingStrategy,
    ExceptionHandlerMiddleware,
    aws_lambda_exception_handler_middleware,
)

pytestmark = pytest.mark.anyio


# Security test payloads for information leakage testing
SENSITIVE_DATA_PAYLOADS = [
    # Database connection strings
    "postgresql://user:password@localhost:5432/db",
    "mongodb://admin:secret@cluster.mongodb.net/database",
    # API keys and tokens
    "sk-1234567890abcdef1234567890abcdef",
    "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "x-api-key: abc123def456",
    # File paths and system information
    "/etc/passwd",
    "C:\\Windows\\System32\\config\\SAM",
    "/home/user/.ssh/id_rsa",
    # Internal system details
    "internal-service-endpoint:8080",
    "admin-panel-url:3000",
    "debug-mode:true",
    # Personal information
    "ssn:123-45-6789",
    "credit-card:4111-1111-1111-1111",
    "email:admin@company.com",
]

MALICIOUS_INPUT_PAYLOADS = [
    # XSS attempts
    "<script>alert('xss')</script>",
    "javascript:alert('xss')",
    "<img src=x onerror=alert('xss')>",
    # SQL injection patterns
    "'; DROP TABLE users; --",
    "1' OR '1'='1",
    "UNION SELECT * FROM users",
    # Command injection
    "; rm -rf /",
    "| cat /etc/passwd",
    "`whoami`",
    # Path traversal
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "/etc/../etc/passwd",
    # LDAP injection
    "*)(uid=*))(|(uid=*",
    "admin)(&(password=*))",
    # NoSQL injection
    '{"$where": "this.password.match(/.*/)"}',
    '{"$ne": null}',
]

# Expected security headers that should be present in error responses
REQUIRED_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
}


@fixture
def mock_lambda_context():
    """Mock AWS Lambda context for testing."""
    context = MagicMock()
    context.function_name = "test-function"
    context.request_id = "test-request-123"
    context.remaining_time_in_millis = 30000
    return context


@fixture
def exception_handler_middleware():
    """Create exception handler middleware for security testing."""
    return aws_lambda_exception_handler_middleware(
        name="security_test_handler",
        expose_internal_details=False,  # Security: don't expose internal details
        include_stack_trace=False,  # Security: don't include stack traces
    )


@fixture
def exception_handler_with_internal_details():
    """Create exception handler middleware that exposes internal details for testing."""
    return aws_lambda_exception_handler_middleware(
        name="internal_details_test_handler",
        expose_internal_details=True,
        include_stack_trace=True,
    )


class TestExceptionHandlerSecurityHeaders:
    """Test security headers in exception handler responses."""

    async def test_exception_handler_security_headers(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Includes security headers in responses.

        Security test that ensures the exception handler middleware includes
        appropriate security headers in all error responses to prevent
        common web vulnerabilities.
        """
        # Create event that will trigger an exception
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for security headers")

        # Security test: Should include security headers in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should include headers
        assert "headers" in result, "Error response should include headers"

        response_headers = result["headers"]

        # Security assertion: All required security headers should be present
        for header_name, expected_value in REQUIRED_SECURITY_HEADERS.items():
            assert (
                header_name in response_headers
            ), f"Missing security header: {header_name}"
            assert (
                response_headers[header_name] == expected_value
            ), f"Invalid value for {header_name}"

    async def test_exception_handler_security_headers_cors_integration(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Security headers work correctly with CORS headers.

        Security test that ensures security headers are properly included
        alongside CORS headers without conflicts.
        """
        # Create event that will trigger an exception
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for CORS integration")

        # Security test: Should include both security and CORS headers
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should include headers
        assert "headers" in result, "Error response should include headers"

        response_headers = result["headers"]

        # Security assertion: Security headers should be present
        for header_name in REQUIRED_SECURITY_HEADERS:
            assert (
                header_name in response_headers
            ), f"Missing security header: {header_name}"

    async def test_exception_handler_security_headers_validation_error(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Security headers included in validation error responses.

        Security test that ensures security headers are included even
        for validation errors (4xx status codes).
        """
        # Create event that will trigger a validation error
        event = {"test": "data"}

        # Mock handler that raises a validation error
        async def failing_handler(event, context):
            # Use ValueError which maps to VALIDATION_ERROR (4xx status)
            raise ValueError("Validation failed: required field missing")

        # Security test: Should include security headers in validation error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should include headers
        assert "headers" in result, "Error response should include headers"

        response_headers = result["headers"]

        # Security assertion: Security headers should be present for validation errors
        for header_name in REQUIRED_SECURITY_HEADERS:
            assert (
                header_name in response_headers
            ), f"Missing security header: {header_name}"

    async def test_exception_handler_security_headers_internal_error(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Security headers included in internal error responses.

        Security test that ensures security headers are included even
        for internal server errors (5xx status codes).
        """
        # Create event that will trigger an internal error
        event = {"test": "data"}

        # Mock handler that raises an internal error
        async def failing_handler(event, context):
            raise RuntimeError("Internal server error")

        # Security test: Should include security headers in internal error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should include headers
        assert "headers" in result, "Error response should include headers"

        response_headers = result["headers"]

        # Security assertion: Security headers should be present for internal errors
        for header_name in REQUIRED_SECURITY_HEADERS:
            assert (
                header_name in response_headers
            ), f"Missing security header: {header_name}"


class TestExceptionHandlerErrorInformationLeakage:
    """Test prevention of information leakage in exception handler responses."""

    @pytest.mark.parametrize("sensitive_data", SENSITIVE_DATA_PAYLOADS)
    async def test_exception_handler_error_information_leakage(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
        sensitive_data: str,
    ):
        """Prevents information leakage.

        Security test that ensures the exception handler middleware does not
        leak sensitive information in error responses, even when such information
        is present in the error context or exception messages.
        """
        # Create event that will trigger an exception with sensitive data
        event = {"test": "data", "sensitive": sensitive_data}

        # Mock handler that raises an exception with sensitive data
        async def failing_handler(event, context):
            raise ValueError(f"Error with sensitive data: {sensitive_data}")

        # Security test: Should not leak sensitive information in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should not contain sensitive data
        result_str = json.dumps(result, default=str).lower()

        # Security assertion: Sensitive data should not be present in response
        assert (
            sensitive_data.lower() not in result_str
        ), f"Sensitive data leaked in response: {sensitive_data}"

        # Security assertion: Common sensitive patterns should not be present
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "connection",
            "database",
            "admin",
            "internal",
        ]

        for pattern in sensitive_patterns:
            if pattern in sensitive_data.lower():
                assert (
                    pattern not in result_str
                ), f"Sensitive pattern '{pattern}' leaked in response"

    @pytest.mark.parametrize("malicious_input", MALICIOUS_INPUT_PAYLOADS)
    async def test_exception_handler_malicious_input_sanitization(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
        malicious_input: str,
    ):
        """Sanitizes malicious input in error responses.

        Security test that ensures the exception handler middleware properly
        sanitizes malicious input to prevent XSS, injection, and other attacks
        in error responses.
        """
        # Create event that will trigger an exception with malicious input
        event = {"test": "data", "malicious": malicious_input}

        # Mock handler that raises an exception with malicious input
        async def failing_handler(event, context):
            raise ValueError(f"Error with malicious input: {malicious_input}")

        # Security test: Should sanitize malicious input in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should not contain unsanitized malicious input
        result_str = json.dumps(result, default=str)

        # Security assertion: Malicious input should be sanitized or removed
        assert (
            malicious_input not in result_str
        ), f"Malicious input not sanitized: {malicious_input}"

        # Security assertion: Common attack patterns should be sanitized
        attack_patterns = [
            "<script>",
            "javascript:",
            "onerror=",
            "onload=",
            "'; DROP",
            "UNION SELECT",
        ]

        for pattern in attack_patterns:
            if pattern in malicious_input:
                assert (
                    pattern not in result_str
                ), f"Attack pattern '{pattern}' not sanitized"

    async def test_exception_handler_stack_trace_protection(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Prevents stack trace leakage in production.

        Security test that ensures the exception handler middleware does not
        leak stack traces or internal implementation details in error responses
        when configured for production security.
        """
        # Create event that will trigger an exception
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for stack trace protection")

        # Security test: Should not include stack traces in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should not contain stack trace information
        result_str = json.dumps(result, default=str)

        # Security assertion: Stack trace patterns should not be present
        stack_trace_patterns = [
            "Traceback",
            'File "',
            "line ",
            "in ",
            "raise ",
            "Exception:",
            "Error:",
            "at 0x",
            "built-in",
        ]

        for pattern in stack_trace_patterns:
            assert (
                pattern not in result_str
            ), f"Stack trace pattern '{pattern}' leaked in response"

    async def test_exception_handler_internal_details_protection(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Prevents internal implementation details leakage.

        Security test that ensures the exception handler middleware does not
        leak internal implementation details, file paths, or system information
        in error responses.
        """
        # Create event that will trigger an exception
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for internal details protection")

        # Security test: Should not include internal details in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should not contain internal implementation details
        result_str = json.dumps(result, default=str)

        # Security assertion: Internal details patterns should not be present
        internal_patterns = [
            "/src/",
            "/home/",
            "/var/",
            "C:\\",
            "ExceptionHandlerMiddleware",
            "AWSLambdaErrorHandlingStrategy",
            "error_handling",
            "middleware",
        ]

        for pattern in internal_patterns:
            assert (
                pattern not in result_str
            ), f"Internal detail pattern '{pattern}' leaked in response"

    async def test_exception_handler_correlation_id_safety(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Ensures correlation ID doesn't leak sensitive information.

        Security test that ensures correlation IDs used for tracking don't
        accidentally leak sensitive information or become attack vectors.
        """
        # Create event that will trigger an exception
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for correlation ID safety")

        # Security test: Should include safe correlation ID in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should include correlation ID
        assert (
            "correlation_id" in result
        ), "Error response should include correlation_id"

        correlation_id = result["correlation_id"]

        # Security assertion: Correlation ID should be safe (no sensitive patterns)
        assert correlation_id is not None, "Correlation ID should not be None"
        assert isinstance(correlation_id, str), "Correlation ID should be a string"

        # Security assertion: Correlation ID should not contain sensitive patterns
        sensitive_patterns = ["password", "secret", "key", "token", "admin", "internal"]

        for pattern in sensitive_patterns:
            assert (
                pattern not in correlation_id.lower()
            ), f"Correlation ID contains sensitive pattern: {pattern}"

    async def test_exception_handler_error_type_safety(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Ensures error types don't leak sensitive information.

        Security test that ensures error type categorization doesn't
        accidentally leak sensitive information about the system.
        """
        # Create event that will trigger an exception
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for error type safety")

        # Security test: Should include safe error type in error response
        result = await exception_handler_middleware(
            failing_handler, event, mock_lambda_context
        )

        # Security assertion: Response should include error type
        assert "error_type" in result, "Error response should include error_type"

        error_type = result["error_type"]

        # Security assertion: Error type should be a valid enum value
        valid_error_types = [e.value for e in ErrorType]
        assert error_type in valid_error_types, f"Invalid error type: {error_type}"

        # Security assertion: Error type should not contain sensitive information
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "admin",
            "internal",
            "database",
        ]

        for pattern in sensitive_patterns:
            assert (
                pattern not in error_type.lower()
            ), f"Error type contains sensitive pattern: {pattern}"


class TestExceptionHandlerInputValidation:
    """Test input validation and sanitization in exception handler."""

    async def test_exception_handler_malformed_event_handling(
        self,
        exception_handler_middleware: ExceptionHandlerMiddleware,
        mock_lambda_context,
    ):
        """Handles malformed events securely.

        Security test that ensures the exception handler middleware handles
        malformed or malicious events without leaking information or crashing.
        """
        # Create malformed event
        malformed_event = {
            "malicious": "<script>alert('xss')</script>",
            "injection": "'; DROP TABLE users; --",
            "path_traversal": "../../../etc/passwd",
            "null_bytes": "test\x00string",
        }

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for malformed event handling")

        # Security test: Should handle malformed event securely
        result = await exception_handler_middleware(
            failing_handler, malformed_event, mock_lambda_context
        )

        # Security assertion: Response should be valid JSON
        assert isinstance(result, dict), "Error response should be a dictionary"

        # Security assertion: Response should not contain malformed data
        result_str = json.dumps(result, default=str)

        # Security assertion: Malicious patterns should be sanitized
        malicious_patterns = ["<script>", "'; DROP", "../", "\x00"]

        for pattern in malicious_patterns:
            assert (
                pattern not in result_str
            ), f"Malicious pattern '{pattern}' not sanitized"

    async def test_exception_handler_context_injection_protection(
        self, exception_handler_middleware: ExceptionHandlerMiddleware
    ):
        """Prevents context injection attacks.

        Security test that ensures the exception handler middleware prevents
        context injection attacks through malicious context objects.
        """
        # Create malicious context
        malicious_context = MagicMock()
        malicious_context.function_name = "<script>alert('xss')</script>"
        malicious_context.request_id = "'; DROP TABLE users; --"
        malicious_context.remaining_time_in_millis = 30000

        # Create event
        event = {"test": "data"}

        # Mock handler that raises an exception
        async def failing_handler(event, context):
            raise ValueError("Test error for context injection protection")

        # Security test: Should handle malicious context securely
        result = await exception_handler_middleware(
            failing_handler, event, malicious_context
        )

        # Security assertion: Response should be valid
        assert isinstance(result, dict), "Error response should be a dictionary"

        # Security assertion: Response should not contain malicious context data
        result_str = json.dumps(result, default=str)

        # Security assertion: Malicious context data should be sanitized
        malicious_patterns = ["<script>", "'; DROP"]

        for pattern in malicious_patterns:
            assert (
                pattern not in result_str
            ), f"Malicious context pattern '{pattern}' not sanitized"
