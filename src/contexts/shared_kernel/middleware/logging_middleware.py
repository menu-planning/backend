"""
Logging middleware for standardized endpoint request/response logging.

This middleware provides consistent structured logging across all endpoints with:
- Correlation ID generation and lifecycle management
- Request/response logging with configurable detail levels
- Performance tracking and monitoring
- Integration with existing logging infrastructure
- Error context capture and structured reporting
"""

import json
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from src.logging.logger import StructlogFactory, correlation_id_ctx, set_correlation_id
from src.logging.logger import logger as standard_logger


class LoggingMiddleware:
    """
    Middleware for standardized endpoint logging with correlation ID management.

    Features:
    - Automatic correlation ID generation and context management
    - Structured request/response logging
    - Performance monitoring with execution time tracking
    - Configurable log detail levels for different environments
    - Integration with existing error schemas and lambda exception handler
    - ELK-compatible structured log format
    """

    def __init__(
        self,
        *,
        logger_name: str = "endpoint",
        log_request_body: bool = True,
        log_response_body: bool = True,
        max_body_size: int = 1000,
        performance_warning_threshold: float = 5.0,
    ):
        """
        Initialize logging middleware.

        Args:
            logger_name: Name for the logger instance
            log_request_body: Whether to log request body content
            log_response_body: Whether to log response body content
            max_body_size: Maximum body size to log (truncate if larger)
            performance_warning_threshold: Warn if execution time exceeds
                threshold (seconds)
        """
        # Ensure structlog is configured
        StructlogFactory.configure()

        self.structured_logger = StructlogFactory.get_logger(logger_name)
        self.standard_logger = standard_logger

        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.performance_warning_threshold = performance_warning_threshold

    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID for request tracking.

        Returns:
            8-character hex correlation ID
        """
        return uuid.uuid4().hex[:8]

    def extract_user_context(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Extract user context from Lambda event for logging.

        Args:
            event: Lambda event dictionary

        Returns:
            Dictionary with user context information
        """
        try:
            authorizer_context = event.get("requestContext", {}).get("authorizer")
            if authorizer_context:
                claims = authorizer_context.get("claims", {})
                return {
                    "user_id": claims.get("sub"),
                    "username": claims.get("cognito:username"),
                    "auth_time": claims.get("auth_time"),
                }
        except (AttributeError, KeyError):
            pass

        return {"user_id": None, "auth_method": "localstack_bypass"}

    def sanitize_body_for_logging(self, body: Any) -> Any:
        """
        Sanitize request/response body for safe logging.

        Args:
            body: Body content to sanitize

        Returns:
            Sanitized body safe for logging
        """
        if body is None:
            return None

        # Convert to string if not already
        if isinstance(body, dict):
            body_str = json.dumps(body)
        elif isinstance(body, str):
            body_str = body
        else:
            body_str = str(body)

        # Truncate if too large
        if len(body_str) > self.max_body_size:
            return body_str[: self.max_body_size] + "... [TRUNCATED]"

        return body_str

    def extract_request_metadata(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Extract request metadata for structured logging.

        Args:
            event: Lambda event dictionary

        Returns:
            Dictionary with request metadata
        """
        headers = event.get("headers") or {}
        return {
            "http_method": event.get("httpMethod", "UNKNOWN"),
            "resource_path": event.get("resource"),
            "path_parameters": event.get("pathParameters"),
            "query_parameters": event.get("queryStringParameters"),
            "multi_value_query_parameters": event.get(
                "multiValueQueryStringParameters"
            ),
            "headers": {
                k: v
                for k, v in headers.items()
                if k.lower() not in ["authorization", "cookie"]  # Exclude sensitive
            },
            "source_ip": (
                event.get("requestContext", {}).get("identity", {}).get("sourceIp")
            ),
            "user_agent": headers.get("User-Agent"),
            "request_id": event.get("requestContext", {}).get("requestId"),
        }

    @asynccontextmanager
    async def log_request_response(
        self, event: dict[str, Any], context: Any, correlation_id: str | None = None
    ):
        """
        Context manager for request/response logging with timing.

        Args:
            event: Lambda event dictionary
            context: Lambda context object
            correlation_id: Optional correlation ID (generated if not provided)

        Yields:
            Dictionary with operation context and correlation_id
        """
        # Generate or use provided correlation ID
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()

        # Set correlation ID in context for this request
        correlation_token = correlation_id_ctx.set(correlation_id)

        # Also set via legacy function for backward compatibility
        set_correlation_id(correlation_id)

        start_time = time.perf_counter()
        request_metadata = self.extract_request_metadata(event)
        user_context = self.extract_user_context(event)

        # Parse request body for logging
        request_body = None
        if self.log_request_body and event.get("body"):
            try:
                request_body = json.loads(event["body"])
            except (json.JSONDecodeError, TypeError):
                request_body = event["body"]

        # Create operation context
        operation_context = {
            "correlation_id": correlation_id,
            "start_time": start_time,
            "request_metadata": request_metadata,
            "user_context": user_context,
        }

        # Log request start
        self.structured_logger.info(
            "Endpoint request started",
            correlation_id=correlation_id,
            http_method=request_metadata["http_method"],
            resource_path=request_metadata["resource_path"],
            user_id=user_context.get("user_id"),
            path_parameters=request_metadata["path_parameters"],
            query_parameters=request_metadata["query_parameters"],
            request_body=(
                self.sanitize_body_for_logging(request_body)
                if self.log_request_body
                else None
            ),
            source_ip=request_metadata["source_ip"],
            user_agent=request_metadata["user_agent"],
            aws_request_id=request_metadata["request_id"],
        )

        try:
            yield operation_context

        except Exception as e:
            # Log error context
            execution_time = time.perf_counter() - start_time

            self.structured_logger.error(
                "Endpoint request failed",
                correlation_id=correlation_id,
                execution_time=execution_time,
                error_type=type(e).__name__,
                error_message=str(e),
                http_method=request_metadata["http_method"],
                resource_path=request_metadata["resource_path"],
                user_id=user_context.get("user_id"),
            )
            raise

        finally:
            # Reset correlation ID context
            correlation_id_ctx.reset(correlation_token)

    def log_response(
        self, response: dict[str, Any], operation_context: dict[str, Any]
    ) -> None:
        """
        Log endpoint response with performance metrics.

        Args:
            response: Lambda response dictionary
            operation_context: Context from log_request_response
        """
        execution_time = time.perf_counter() - operation_context["start_time"]
        correlation_id = operation_context["correlation_id"]
        request_metadata = operation_context["request_metadata"]
        user_context = operation_context["user_context"]

        # Parse response body for logging
        response_body = None
        if self.log_response_body and response.get("body"):
            try:
                response_body = json.loads(response["body"])
            except (json.JSONDecodeError, TypeError):
                response_body = response["body"]

        # Log successful response
        self.structured_logger.info(
            "Endpoint request completed",
            correlation_id=correlation_id,
            execution_time=execution_time,
            status_code=response.get("statusCode"),
            http_method=request_metadata["http_method"],
            resource_path=request_metadata["resource_path"],
            user_id=user_context.get("user_id"),
            response_body=(
                self.sanitize_body_for_logging(response_body)
                if self.log_response_body
                else None
            ),
            response_headers=response.get("headers", {}),
            success=200 <= (response.get("statusCode", 500)) < 400,
        )

        # Performance warning if execution time exceeds threshold
        if execution_time > self.performance_warning_threshold:
            self.structured_logger.warning(
                "Endpoint performance warning",
                correlation_id=correlation_id,
                execution_time=execution_time,
                threshold=self.performance_warning_threshold,
                http_method=request_metadata["http_method"],
                resource_path=request_metadata["resource_path"],
                user_id=user_context.get("user_id"),
            )

    async def __call__(
        self, handler: Callable[[dict[str, Any], Any], Awaitable[dict[str, Any]]]
    ) -> Callable[[dict[str, Any], Any], Awaitable[dict[str, Any]]]:
        """
        Make the middleware callable as a decorator.

        Args:
            handler: The endpoint handler function

        Returns:
            Wrapped handler with logging middleware
        """

        async def wrapped_handler(
            event: dict[str, Any], context: Any
        ) -> dict[str, Any]:
            async with self.log_request_response(event, context) as operation_context:
                response = await handler(event, context)
                self.log_response(response, operation_context)
                return response

        return wrapped_handler


# Convenience function for creating logging middleware with default settings
def create_logging_middleware(
    logger_name: str = "endpoint",
    log_request_body: bool = True,
    log_response_body: bool = True,
    max_body_size: int = 1000,
    performance_warning_threshold: float = 5.0,
) -> LoggingMiddleware:
    """
    Create a logging middleware instance with specified configuration.

    Args:
        logger_name: Name for the logger instance
        log_request_body: Whether to log request body content
        log_response_body: Whether to log response body content
        max_body_size: Maximum body size to log (truncate if larger)
        performance_warning_threshold: Warn if execution time exceeds
            threshold (seconds)

    Returns:
        Configured LoggingMiddleware instance
    """
    return LoggingMiddleware(
        logger_name=logger_name,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        max_body_size=max_body_size,
        performance_warning_threshold=performance_warning_threshold,
    )


# Pre-configured middleware instances for common use cases
standard_logging_middleware = create_logging_middleware()
minimal_logging_middleware = create_logging_middleware(
    log_request_body=False, log_response_body=False, max_body_size=500
)
performance_focused_middleware = create_logging_middleware(
    performance_warning_threshold=2.0, max_body_size=500
)
