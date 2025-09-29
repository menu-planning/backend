"""FastAPI logging middleware integrating with the comprehensive structured logging system.

This middleware provides FastAPI-specific logging that integrates with the existing
structured logging middleware system, providing consistent logging patterns across
AWS Lambda and FastAPI platforms.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    LoggingStrategy,
    StructuredLoggingMiddleware,
)
from src.contexts.shared_kernel.middleware.logging.sensitive_data_redactor import (
    sensitive_data_redactor,
)
from src.logging.logger import get_logger


class FastAPILoggingStrategy(LoggingStrategy):
    """FastAPI-specific logging strategy.

    Extracts logging context from FastAPI Request objects and integrates
    with the existing structured logging system.

    Notes:
        Handles FastAPI Request objects specifically.
        Extracts request metadata and user context.
    """

    def extract_logging_context(self, *args, **kwargs) -> dict[str, any]:
        """Extract logging context from FastAPI Request.

        Args:
            *args: Positional arguments (request, call_next).
            **kwargs: Keyword arguments (request, call_next).

        Returns:
            Dictionary with logging context information.
        """
        request = self.get_request_data(*args, **kwargs)[0]

        # Extract FastAPI request context information
        logging_context = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }

        # Add correlation ID if available
        correlation_id = request.headers.get("x-correlation-id")
        if correlation_id:
            logging_context["correlation_id"] = correlation_id

        # Add user context if available
        if hasattr(request, "state") and hasattr(request.state, "user"):
            logging_context["user_id"] = getattr(request.state.user, "id", None)

        # Create request summary with redaction
        request_summary = self._get_request_summary(request)
        logging_context["request_summary"] = sensitive_data_redactor.redact_data(
            request_summary
        )

        return logging_context

    def get_request_data(self, *args, **kwargs) -> tuple[Request, any]:
        """Extract FastAPI Request from middleware arguments.

        Args:
            *args: Positional arguments (request, call_next)
            **kwargs: Keyword arguments (request, call_next)

        Returns:
            Tuple of (request, call_next)

        Raises:
            ValueError: If request is missing
        """
        request: Request | None = (
            kwargs.get("request") if "request" in kwargs else args[0] if args else None
        )
        call_next = (
            kwargs.get("call_next")
            if "call_next" in kwargs
            else args[1] if len(args) > 1 else None
        )

        if not request:
            error_message = "Request is required for FastAPI logging"
            raise ValueError(error_message)

        return request, call_next

    def inject_logging_context(
        self, request_data: dict[str, any], logging_context: dict[str, any]
    ) -> None:
        """Inject logging context into request state.

        Args:
            request_data: The request data dictionary
            logging_context: The logging context to inject
        """
        # For FastAPI, we inject into request state
        if hasattr(request_data, "state"):
            request_data.state._logging_context = logging_context

    def _get_request_summary(self, request: Request) -> dict[str, any]:
        """Generate a summary of the request for logging."""
        summary = {
            "method": request.method,
            "path": request.url.path,
            "scheme": request.url.scheme,
            "host": request.url.hostname,
            "port": request.url.port,
        }

        # Add query parameters count
        if request.query_params:
            summary["query_params_count"] = len(request.query_params)

        # Add headers count
        summary["headers_count"] = len(request.headers)

        return summary


class FastAPILoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI logging middleware integrating with the structured logging system.

    This middleware integrates with the existing comprehensive structured logging
    system by using the StructuredLoggingMiddleware with a FastAPI-specific strategy.

    Attributes:
        structured_middleware: The underlying structured logging middleware.
        logger: Logger instance for logging.

    Notes:
        Order: runs first in middleware chain (captures everything).
        Uses the comprehensive structured logging system for consistency.
    """

    def __init__(
        self,
        app,
        *,
        name: str | None = None,
        logger_name: str = "fastapi_logging",
        log_request: bool = True,
        log_response: bool = True,
        log_timing: bool = True,
        log_correlation_id: bool = True,
        include_request_summary: bool = False,
        include_response_summary: bool = False,
    ):
        """Initialize FastAPI logging middleware.

        Args:
            app: FastAPI application instance.
            name: Optional name for the middleware.
            logger_name: Name for the logger instance.
            log_request: Whether to log incoming requests.
            log_response: Whether to log response information.
            log_timing: Whether to log timing information.
            log_correlation_id: Whether to log correlation IDs.
            include_request_summary: Whether to include request summary (dev only).
            include_response_summary: Whether to include response summary (dev only).
        """
        super().__init__(app)

        # Create FastAPI-specific strategy
        strategy = FastAPILoggingStrategy()

        # Create the underlying structured logging middleware
        self.structured_middleware = StructuredLoggingMiddleware(
            strategy=strategy,
            name=name,
            logger_name=logger_name,
            log_request=log_request,
            log_response=log_response,
            log_timing=log_timing,
            log_correlation_id=log_correlation_id,
            include_event_summary=include_request_summary,
            include_response_summary=include_response_summary,
        )

        self.logger = get_logger(logger_name)

    async def dispatch(self, request: Request, call_next):
        """Execute logging middleware around the request.

        Args:
            request: FastAPI Request object.
            call_next: Next middleware/handler in the chain.

        Returns:
            Either successful response or passes through exceptions.

        Notes:
            Uses the comprehensive structured logging system for consistent
            logging patterns across platforms.
        """
        try:
            # Create a simple handler function for the structured middleware
            async def handler(*args, **kwargs):
                return await call_next(request)

            # Call the structured logging middleware with FastAPI context
            return await self.structured_middleware(
                handler, request, call_next
            )

        except Exception as exc:
            # Let the structured middleware handle error logging
            # Re-raise the exception for error handling middleware
            raise


# Convenience function for creating FastAPI logging middleware
def create_fastapi_logging_middleware(
    *,
    name: str | None = None,
    logger_name: str = "fastapi_logging",
    log_request: bool = True,
    log_response: bool = True,
    log_timing: bool = True,
    log_correlation_id: bool = True,
    include_request_summary: bool = False,
    include_response_summary: bool = False,
) -> type[FastAPILoggingMiddleware]:
    """Create FastAPI logging middleware with common configuration.

    Args:
        name: Optional middleware name.
        logger_name: Name for the logger instance.
        log_request: Whether to log incoming requests.
        log_response: Whether to log response information.
        log_timing: Whether to log timing information.
        log_correlation_id: Whether to log correlation IDs.
        include_request_summary: Whether to include request summary (dev only).
        include_response_summary: Whether to include response summary (dev only).

    Returns:
        Configured FastAPILoggingMiddleware class.

    Notes:
        Creates FastAPILoggingMiddleware with specified configuration.
        Provides a convenient factory function for common logging setups.
    """
    class ConfiguredFastAPILoggingMiddleware(FastAPILoggingMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                name=name,
                logger_name=logger_name,
                log_request=log_request,
                log_response=log_response,
                log_timing=log_timing,
                log_correlation_id=log_correlation_id,
                include_request_summary=include_request_summary,
                include_response_summary=include_response_summary,
            )

    return ConfiguredFastAPILoggingMiddleware
