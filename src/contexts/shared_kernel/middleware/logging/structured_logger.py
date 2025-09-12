"""Structured logging middleware for consistent logging with correlation IDs.

This middleware provides unified logging across all endpoints by:
- Automatically capturing correlation IDs from context
- Logging request/response lifecycle events
- Providing structured logging with consistent fields
- Integration with existing logging infrastructure
- Performance metrics and timing information
- Platform-agnostic design using strategy pattern
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.contexts.shared_kernel.middleware.logging.sensitive_data_redactor import (
    sensitive_data_redactor,
)
from src.logging.logger import StructlogFactory, correlation_id_ctx


class LoggingStrategy(ABC):
    """Abstract base class for logging strategies.

    This interface defines how different platforms (AWS Lambda, FastAPI, etc.)
    should implement logging context extraction and request data handling.

    Notes:
        All methods must be implemented by concrete strategy classes.
        Platform-specific implementations handle different request formats.
    """

    @abstractmethod
    def extract_logging_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract logging context from the request.

        Args:
            *args: Positional arguments from the middleware call.
            **kwargs: Keyword arguments from the middleware call.

        Returns:
            Dictionary with logging context information.
        """

    @abstractmethod
    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Extract request data from the middleware arguments.

        Args:
            *args: Positional arguments from the middleware call.
            **kwargs: Keyword arguments from the middleware call.

        Returns:
            Tuple of (request_data, context).
        """

    @abstractmethod
    def inject_logging_context(
        self, request_data: dict[str, Any], logging_context: dict[str, Any]
    ) -> None:
        """Inject logging context into the request data.

        Args:
            request_data: The request data to modify.
            logging_context: The logging context to inject.
        """


class AWSLambdaLoggingStrategy(LoggingStrategy):
    """AWS Lambda-specific logging strategy.

    Extracts logging context from AWS Lambda events and context objects.

    Notes:
        Handles AWS Lambda event and context objects specifically.
        Extracts function metadata and request information.
    """

    def extract_logging_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract logging context from AWS Lambda event and context.

        Args:
            *args: Positional arguments (event, context).
            **kwargs: Keyword arguments (event, context).

        Returns:
            Dictionary with logging context information.
        """
        event, context = self.get_request_data(*args, **kwargs)

        # Extract AWS Lambda context information
        logging_context = {}

        if hasattr(context, "function_name"):
            logging_context["function_name"] = context.function_name
        if hasattr(context, "function_version"):
            logging_context["function_version"] = context.function_version
        if hasattr(context, "request_id"):
            logging_context["request_id"] = context.request_id
        if hasattr(context, "memory_limit_in_mb"):
            logging_context["memory_limit_mb"] = context.memory_limit_in_mb
        if hasattr(context, "remaining_time_in_millis"):
            logging_context["remaining_time_ms"] = context.remaining_time_in_millis

        # Add event summary with redaction
        event_summary = self._get_event_summary(event)
        logging_context["event_summary"] = sensitive_data_redactor.redact_data(
            event_summary
        )

        return logging_context

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """
        Extract AWS Lambda event and context from middleware arguments.

        Args:
            *args: Positional arguments (event, context)
            **kwargs: Keyword arguments (event, context)

        Returns:
            Tuple of (event, context)
        """
        event: dict[str, Any] | None = (
            kwargs.get("event") if "event" in kwargs else args[0]
        )
        context: Any = kwargs.get("context") if "context" in kwargs else args[1]

        if not event or not context:
            error_message = "Event and context are required"
            raise ValueError(error_message)

        return event, context

    def inject_logging_context(
        self, request_data: dict[str, Any], logging_context: dict[str, Any]
    ) -> None:
        """
        Inject logging context into AWS Lambda event.

        Args:
            request_data: The AWS Lambda event dictionary
            logging_context: The logging context to inject
        """
        request_data["_logging_context"] = logging_context

    def _get_event_summary(self, event: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of the event for logging."""
        summary = {
            "event_type": event.get("type", "unknown"),
            "event_source": event.get("source", "unknown"),
            "event_id": event.get("id", "unknown"),
        }

        # Add HTTP method and path if available
        if "httpMethod" in event:
            summary["http_method"] = event["httpMethod"]
        if "path" in event:
            summary["path"] = event["path"]
        if "resource" in event:
            summary["resource"] = event["resource"]

        return summary


class StructuredLoggingMiddleware(BaseMiddleware):
    """Generic structured logging middleware that uses composition for different strategies.

    Provides simple, consistent logging across different platforms while
    maintaining the composable architecture. It delegates platform-specific
    logging logic to strategy objects.

    Attributes:
        strategy: The logging strategy to use.
        logger: Logger instance for structured logging.
        log_request: Whether to log incoming requests.
        log_response: Whether to log response information.
        log_timing: Whether to log timing information.
        log_correlation_id: Whether to log correlation IDs.
        include_event_summary: Whether to include event summary (dev only).
        include_response_summary: Whether to include response summary (dev only).

    Notes:
        Order: runs first in middleware chain (captures everything).
        Propagates cancellation: Yes.
        Adds headers: Logging context.
        Retries: None; Timeout: none (observes timeouts).
    """

    def __init__(
        self,
        *,
        strategy: LoggingStrategy,
        name: str | None = None,
        logger_name: str = "middleware.logging",
        log_request: bool = True,
        log_response: bool = True,
        log_timing: bool = True,
        log_correlation_id: bool = True,
        include_event_summary: bool = False,
        include_response_summary: bool = False,
        include_event: bool = False,
    ):
        """Initialize structured logging middleware.

        Args:
            strategy: The logging strategy to use.
            name: Optional name for the middleware.
            logger_name: Name for the logger instance.
            log_request: Whether to log incoming requests.
            log_response: Whether to log response information.
            log_timing: Whether to log timing information.
            log_correlation_id: Whether to log correlation IDs.
            include_event_summary: Whether to include event summary (dev only).
            include_response_summary: Whether to include response summary (dev only).
            include_event: Whether to include full event data in logs (dev only).
        """
        super().__init__(name=name)

        # Ensure structlog is configured
        StructlogFactory.configure()

        self.strategy = strategy
        self.logger = StructlogFactory.get_logger(logger_name)
        self.log_request = log_request
        self.log_response = log_response
        self.log_timing = log_timing
        self.log_correlation_id = log_correlation_id
        self.include_event_summary = include_event_summary
        self.include_response_summary = include_response_summary
        self.include_event = include_event

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute structured logging middleware around the handler.

        Args:
            handler: The next handler in the middleware chain.
            *args: Positional arguments passed to the middleware.
            **kwargs: Keyword arguments passed to the middleware.

        Returns:
            The response from the handler (potentially modified).

        Notes:
            Logs request start, extracts logging context, executes handler,
            and logs response with timing information.
        """
        start_time = time.time()

        # Extract logging context using the strategy
        logging_context = self.strategy.extract_logging_context(*args, **kwargs)

        # Capture correlation ID from context
        correlation_id = correlation_id_ctx.get()

        # Log request start
        if self.log_request:
            request_data, _ = self.strategy.get_request_data(*args, **kwargs)
            self._log_request_start(logging_context, correlation_id, request_data)

        try:
            # Get request data and inject logging context
            request_data, context = self.strategy.get_request_data(*args, **kwargs)
            self.strategy.inject_logging_context(request_data, logging_context)

            # Execute handler
            response = await handler(request_data, context)

            # Calculate timing
            execution_time = time.time() - start_time

            # Log successful response
            if self.log_response:
                self._log_response_success(
                    response, logging_context, correlation_id, execution_time
                )

        except Exception as e:
            # Calculate timing for error case
            execution_time = time.time() - start_time

            # Log error
            self._log_response_error(e, logging_context, correlation_id, execution_time)

            # Re-raise to let error handling middleware handle it
            raise
        else:
            return response

    def _log_request_start(
        self,
        logging_context: dict[str, Any],
        correlation_id: str,
        event_data: dict[str, Any],
    ) -> None:
        """Log the start of a request."""
        log_data = {
            "log_event": "request_start",
            "correlation_id": correlation_id if self.log_correlation_id else None,
            "timestamp": "now",
        }

        # Add platform-specific context information with redaction
        redacted_logging_context = sensitive_data_redactor.redact_data(logging_context)
        log_data.update(redacted_logging_context)

        if self.include_event_summary:
            log_data["event_summary"] = redacted_logging_context.get("event_summary")

        if self.include_event:
            log_data["lambda_event"] = sensitive_data_redactor.redact_lambda_event(
                event_data
            )

        # Remove None values for cleaner logs
        log_data = {k: v for k, v in log_data.items() if v is not None}

        self.logger.info("Request started", **log_data)

    def _log_response_success(
        self,
        response: dict[str, Any],
        logging_context: dict[str, Any],
        correlation_id: str,
        execution_time: float,
    ) -> None:
        """Log successful response completion."""
        log_data = {
            "log_event": "request_completed",
            "correlation_id": correlation_id if self.log_correlation_id else None,
            "execution_time_ms": (
                round(execution_time * 1000, 2) if self.log_timing else None
            ),
            "status": "success",
            "timestamp": "now",
        }

        # Add platform-specific context information with redaction
        redacted_logging_context = sensitive_data_redactor.redact_data(logging_context)
        log_data.update(redacted_logging_context)

        if self.include_response_summary:
            response_summary = self._get_response_summary(response)
            log_data["response_summary"] = sensitive_data_redactor.redact_data(
                response_summary
            )

        # Remove None values for cleaner logs
        log_data = {k: v for k, v in log_data.items() if v is not None}

        self.logger.info("Request completed successfully", **log_data)

    def _log_response_error(
        self,
        error: Exception,
        logging_context: dict[str, Any],
        correlation_id: str,
        execution_time: float,
    ) -> None:
        """Log error response."""
        log_data = {
            "log_event": "request_failed",
            "correlation_id": correlation_id if self.log_correlation_id else None,
            "execution_time_ms": (
                round(execution_time * 1000, 2) if self.log_timing else None
            ),
            "status": "error",
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "timestamp": "now",
        }

        # Add platform-specific context information with redaction
        redacted_logging_context = sensitive_data_redactor.redact_data(logging_context)
        log_data.update(redacted_logging_context)

        # Remove None values for cleaner logs
        log_data = {k: v for k, v in log_data.items() if v is not None}

        self.logger.error("Request failed", **log_data)

    def _get_response_summary(self, response: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of the response for logging."""
        summary = {
            "status_code": response.get("statusCode", "unknown"),
        }

        # Add response size if available
        if "body" in response:
            body = response["body"]
            if isinstance(body, str):
                summary["response_size_bytes"] = len(body.encode("utf-8"))
            elif isinstance(body, dict | list):
                summary["response_size_bytes"] = len(json.dumps(body).encode("utf-8"))

        return summary

    def get_logging_context(
        self, request_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get logging context from request data.

        Args:
            request_data: The request data dictionary.

        Returns:
            Logging context if available, None otherwise.
        """
        return request_data.get("_logging_context")


# Convenience function for creating structured logging middleware
def create_structured_logging_middleware(
    *,
    strategy: LoggingStrategy,
    name: str | None = None,
    logger_name: str = "middleware.logging",
    log_request: bool = True,
    log_response: bool = True,
    log_timing: bool = True,
    log_correlation_id: bool = True,
    include_event_summary: bool = False,
    include_response_summary: bool = False,
    include_event: bool = False,
) -> StructuredLoggingMiddleware:
    """Create structured logging middleware with common configuration.

    Args:
        strategy: The logging strategy to use.
        name: Optional middleware name.
        logger_name: Name for the logger instance.
        log_request: Whether to log incoming requests.
        log_response: Whether to log response information.
        log_timing: Whether to log timing information.
        log_correlation_id: Whether to log correlation IDs.
        include_event_summary: Whether to include event summary (dev only).
        include_response_summary: Whether to include response summary (dev only).
        include_event: Whether to include full event data in logs (dev only).

    Returns:
        Configured StructuredLoggingMiddleware instance.

    Notes:
        Creates StructuredLoggingMiddleware with specified configuration.
        Provides a convenient factory function for common logging setups.
    """
    return StructuredLoggingMiddleware(
        strategy=strategy,
        name=name,
        logger_name=logger_name,
        log_request=log_request,
        log_response=log_response,
        log_timing=log_timing,
        log_correlation_id=log_correlation_id,
        include_event_summary=include_event_summary,
        include_response_summary=include_response_summary,
        include_event=include_event,
    )


# Factory function for AWS Lambda logging middleware
def aws_lambda_logging_middleware(
    *,
    name: str | None = None,
    logger_name: str = "middleware.logging",
    log_request: bool = True,
    log_response: bool = True,
    log_timing: bool = True,
    log_correlation_id: bool = True,
    include_event_summary: bool = False,
    include_response_summary: bool = False,
    include_event: bool = False,
) -> StructuredLoggingMiddleware:
    """Create structured logging middleware for AWS Lambda.

    Args:
        name: Optional middleware name.
        logger_name: Name for the logger instance.
        log_request: Whether to log incoming requests.
        log_response: Whether to log response information.
        log_timing: Whether to log timing information.
        log_correlation_id: Whether to log correlation IDs.
        include_event_summary: Whether to include event summary (dev only).
        include_response_summary: Whether to include response summary (dev only).
        include_event: Whether to include full event data in logs (dev only).

    Returns:
        Configured StructuredLoggingMiddleware instance for AWS Lambda.

    Notes:
        Uses AWSLambdaLoggingStrategy for AWS Lambda-specific logging.
        Provides a convenient factory function for AWS Lambda logging.
    """
    strategy = AWSLambdaLoggingStrategy()

    return create_structured_logging_middleware(
        strategy=strategy,
        name=name,
        logger_name=logger_name,
        log_request=log_request,
        log_response=log_response,
        log_timing=log_timing,
        log_correlation_id=log_correlation_id,
        include_event_summary=include_event_summary,
        include_response_summary=include_response_summary,
        include_event=include_event,
    )
