"""FastAPI-specific error handling middleware using the comprehensive error handling system.

This middleware integrates with the existing sophisticated error handling system
by providing a FastAPI-specific strategy that works with the shared error handling
infrastructure while maintaining FastAPI response patterns.
"""

from typing import Any
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    ErrorHandlingStrategy,
    ExceptionHandlerMiddleware,
)
from src.logging.logger import get_logger


class FastAPIErrorHandlingStrategy(ErrorHandlingStrategy):
    """FastAPI-specific error handling strategy.

    Extracts error context from FastAPI Request objects and integrates
    with the existing comprehensive error handling system.

    Notes:
        Handles FastAPI Request objects specifically.
        Extracts request metadata and user context.
    """

    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract error context from FastAPI Request.

        Args:
            *args: Positional arguments (request, call_next).
            **kwargs: Keyword arguments (request, call_next).

        Returns:
            Dictionary with error context information.
        """
        request = self.get_request_data(*args, **kwargs)[0]

        # Extract FastAPI request context information
        error_context = {
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
            error_context["correlation_id"] = correlation_id

        # Add user context if available
        if hasattr(request, "state") and hasattr(request.state, "user"):
            error_context["user_id"] = getattr(request.state.user, "id", None)

        return error_context

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[Request, Any]:
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
            error_message = "Request is required for FastAPI error handling"
            raise ValueError(error_message)

        return request, call_next

    def inject_error_context(
        self, request_data: dict[str, Any], error_context: dict[str, Any]
    ) -> None:
        """Inject error context into request state.

        Args:
            request_data: The request data dictionary
            error_context: The error context to inject
        """
        # For FastAPI, we inject into request state
        if hasattr(request_data, "state"):
            request_data.state._error_context = error_context


class FastAPIErrorHandlingMiddleware(BaseHTTPMiddleware):
    """FastAPI error handling middleware using the comprehensive error handling system.

    This middleware integrates with the existing sophisticated error handling
    system by using the ExceptionHandlerMiddleware with a FastAPI-specific strategy.

    Attributes:
        exception_handler: The underlying exception handler middleware.
        logger: Logger instance for error handling.

    Notes:
        Order: runs last in middleware chain (catches all errors).
        Uses the comprehensive error handling system for consistency.
    """

    def __init__(
        self,
        app,
        *,
        name: str | None = None,
        logger_name: str = "fastapi_error_handler",
        include_stack_trace: bool = False,
        expose_internal_details: bool = False,
        default_error_message: str = "An error occurred while processing your request",
    ):
        """Initialize FastAPI error handling middleware.

        Args:
            app: FastAPI application instance.
            name: Optional name for the middleware.
            logger_name: Name for error logger instance.
            include_stack_trace: Whether to include stack traces in error responses.
            expose_internal_details: Whether to expose internal error details to clients.
            default_error_message: Default message for unhandled errors.
        """
        super().__init__(app)

        # Create FastAPI-specific strategy
        strategy = FastAPIErrorHandlingStrategy()

        # Create the underlying exception handler middleware
        self.exception_handler = ExceptionHandlerMiddleware(
            strategy=strategy,
            name=name,
            logger_name=logger_name,
            include_stack_trace=include_stack_trace,
            expose_internal_details=expose_internal_details,
            default_error_message=default_error_message,
        )

        self.logger = get_logger(logger_name)

    async def dispatch(self, request: Request, call_next):
        """Execute error handling middleware around the request.

        Args:
            request: FastAPI Request object.
            call_next: Next middleware/handler in the chain.

        Returns:
            Either successful response or standardized error response.

        Notes:
            Catches all exceptions and converts to standardized error responses
            using the comprehensive error handling system.
        """
        try:
            # Call the next middleware/handler
            response = await call_next(request)
            return response

        except Exception as exc:
            # Use the comprehensive error handling system
            try:
                # Create a simple handler function for the exception handler
                async def handler(*args, **kwargs):
                    raise exc

                # Call the exception handler with FastAPI context
                error_response = await self.exception_handler(
                    handler, request, call_next
                )

                # Convert to FastAPI JSONResponse
                return self._convert_to_fastapi_response(error_response)

            except Exception as handler_exc:
                # Fallback error handling if the exception handler fails
                self.logger.error(
                    "Error in error handler",
                    exc_info=True,
                    handler_error=str(handler_exc),
                    original_error=str(exc),
                )

                # Return a basic error response
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "message": "An unexpected error occurred",
                    },
                )

    def _convert_to_fastapi_response(self, error_response: dict[str, Any]) -> JSONResponse:
        """Convert error response to FastAPI JSONResponse.

        Args:
            error_response: Error response from the exception handler.

        Returns:
            FastAPI JSONResponse with error details.
        """
        # Extract response data
        status_code = error_response.get("statusCode", 500)
        headers = error_response.get("headers", {})
        body = error_response.get("body", {})

        # Create JSONResponse with proper headers
        response = JSONResponse(
            status_code=status_code,
            content=body,
        )

        # Add security headers
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response


# Convenience function for creating FastAPI error handling middleware
def create_fastapi_error_handling_middleware(
    *,
    name: str | None = None,
    logger_name: str = "fastapi_error_handler",
    include_stack_trace: bool = False,
    expose_internal_details: bool = False,
    default_error_message: str = "An error occurred while processing your request",
) -> type[FastAPIErrorHandlingMiddleware]:
    """Create FastAPI error handling middleware with common configuration.

    Args:
        name: Optional middleware name.
        logger_name: Name for error logger instance.
        include_stack_trace: Whether to include stack traces in error responses.
        expose_internal_details: Whether to expose internal error details to clients.
        default_error_message: Default message for unhandled errors.

    Returns:
        Configured FastAPIErrorHandlingMiddleware class.

    Notes:
        Creates FastAPIErrorHandlingMiddleware with specified configuration.
        Provides a convenient factory function for common error handling setups.
    """
    class ConfiguredFastAPIErrorHandlingMiddleware(FastAPIErrorHandlingMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                name=name,
                logger_name=logger_name,
                include_stack_trace=include_stack_trace,
                expose_internal_details=expose_internal_details,
                default_error_message=default_error_message,
            )

    return ConfiguredFastAPIErrorHandlingMiddleware


# Factory function for FastAPI error handling middleware (similar to AWS Lambda pattern)
def fastapi_exception_handler_middleware(
    *,
    name: str | None = None,
    logger_name: str = "fastapi_exception_handler",
    include_stack_trace: bool = False,
    expose_internal_details: bool = False,
    default_error_message: str = "An error occurred while processing your request",
) -> type[FastAPIErrorHandlingMiddleware]:
    """Create exception handler middleware for FastAPI.

    Args:
        name: Optional middleware name.
        logger_name: Name for error logger instance.
        include_stack_trace: Whether to include stack traces in error responses.
        expose_internal_details: Whether to expose internal error details to clients.
        default_error_message: Default message for unhandled errors.

    Returns:
        Configured FastAPIErrorHandlingMiddleware class for FastAPI.

    Notes:
        Uses FastAPIErrorHandlingStrategy for FastAPI-specific error handling.
        Provides a convenient factory function for FastAPI error handling.
        Follows the same pattern as aws_lambda_exception_handler_middleware().
    """
    return create_fastapi_error_handling_middleware(
        name=name,
        logger_name=logger_name,
        include_stack_trace=include_stack_trace,
        expose_internal_details=expose_internal_details,
        default_error_message=default_error_message,
    )