"""
Exception handler middleware for consistent error responses and logging.

This middleware provides standardized error handling across all endpoints by:
- Catching and categorizing all unhandled exceptions
- Converting exceptions to standardized error response schemas
- Supporting exception groups and cancellation propagation
- Integration with logging for correlation ID tracking
- Maintaining backward compatibility with existing error patterns
- Platform-agnostic design using strategy pattern
"""

import traceback

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.contexts.shared_kernel.middleware.error_handling.error_response import (
    ErrorDetail,
    ErrorResponse,
    ErrorType,
)
from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.logging.logger import StructlogFactory, correlation_id_ctx
from src.logging.logger import logger as standard_logger


class ErrorHandlingStrategy(ABC):
    """
    Abstract base class for error handling strategies.

    This interface defines how different platforms (AWS Lambda, FastAPI, etc.)
    should implement error context extraction and request data handling.
    """

    @abstractmethod
    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Extract error context from the request.

        Args:
            *args: Positional arguments from the middleware call
            **kwargs: Keyword arguments from the middleware call

        Returns:
            Dictionary with error context information
        """

    @abstractmethod
    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """
        Extract request data from the middleware arguments.

        Args:
            *args: Positional arguments from the middleware call
            **kwargs: Keyword arguments from the middleware call

        Returns:
            Tuple of (request_data, context)
        """

    @abstractmethod
    def inject_error_context(
        self, request_data: dict[str, Any], error_context: dict[str, Any]
    ) -> None:
        """
        Inject error context into the request data.

        Args:
            request_data: The request data to modify
            error_context: The error context to inject
        """


class AWSLambdaErrorHandlingStrategy(ErrorHandlingStrategy):
    """
    AWS Lambda-specific error handling strategy.

    Extracts error context from AWS Lambda events and context objects.
    """

    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Extract error context from AWS Lambda event and context.

        Args:
            *args: Positional arguments (event, context)
            **kwargs: Keyword arguments (event, context)

        Returns:
            Dictionary with error context information
        """
        event, context = self.get_request_data(*args, **kwargs)

        # Extract AWS Lambda context information
        error_context = {}

        if hasattr(context, "function_name"):
            error_context["function_name"] = context.function_name
        if hasattr(context, "request_id"):
            error_context["request_id"] = context.request_id
        if hasattr(context, "remaining_time_in_millis"):
            error_context["remaining_time_ms"] = context.remaining_time_in_millis

        return error_context

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

    def inject_error_context(
        self, request_data: dict[str, Any], error_context: dict[str, Any]
    ) -> None:
        """
        Inject error context into AWS Lambda event.

        Args:
            request_data: The AWS Lambda event dictionary
            error_context: The error context to inject
        """
        request_data["_error_context"] = error_context


class ExceptionHandlerMiddleware(BaseMiddleware):
    """
    Generic exception handler middleware that uses composition for different strategies.

    This middleware provides simple, consistent error handling across different
    platforms while maintaining the composable architecture. It delegates
    platform-specific error handling logic to strategy objects.
    """

    def __init__(
        self,
        *,
        strategy: ErrorHandlingStrategy,
        name: str | None = None,
        logger_name: str = "exception_handler",
        include_stack_trace: bool = False,
        expose_internal_details: bool = False,
        default_error_message: str = "An error occurred while processing your request",
    ):
        """
        Initialize exception handler middleware.

        Args:
            strategy: The error handling strategy to use
            name: Optional name for the middleware
            logger_name: Name for error logger instance
            include_stack_trace: Whether to include stack traces in error responses
            expose_internal_details: Whether to expose internal error details to clients
            default_error_message: Default message for unhandled errors
        """
        super().__init__(name)

        # Ensure structlog is configured
        StructlogFactory.configure()

        self.strategy = strategy
        self.structured_logger = StructlogFactory.get_logger(logger_name)
        self.standard_logger = standard_logger
        self.include_stack_trace = include_stack_trace
        self.expose_internal_details = expose_internal_details
        self.default_error_message = default_error_message

        # Exception type mappings for automatic categorization
        self.exception_mappings = {
            ValueError: ErrorType.VALIDATION_ERROR,
            TypeError: ErrorType.VALIDATION_ERROR,
            KeyError: ErrorType.NOT_FOUND_ERROR,
            FileNotFoundError: ErrorType.NOT_FOUND_ERROR,
            PermissionError: ErrorType.AUTHORIZATION_ERROR,
            TimeoutError: ErrorType.TIMEOUT_ERROR,
            ConnectionError: ErrorType.TIMEOUT_ERROR,
            ValidationError: ErrorType.VALIDATION_ERROR,
        }

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute exception handler middleware around the handler.

        Args:
            handler: The next handler in the middleware chain
            *args: Positional arguments passed to the middleware
            **kwargs: Keyword arguments passed to the middleware

        Returns:
            Either successful response from handler or standardized error response
        """
        correlation_id = correlation_id_ctx.get() or "unknown"

        try:
            return await handler(*args, **kwargs)

        except ExceptionGroup as exc:
            # Handle exception groups with proper extraction
            error_context = self.strategy.extract_error_context(*args, **kwargs)
            error_response = self._handle_exception_group(
                exc, correlation_id, error_context
            )
        except Exception as exc:
            # Handle single exceptions
            error_context = self.strategy.extract_error_context(*args, **kwargs)
            error_response = self._handle_single_exception(
                exc, correlation_id, error_context
            )

        return error_response

    def _handle_single_exception(
        self, exc: Exception, correlation_id: str, error_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle a single exception and convert to error response.

        Args:
            exc: The exception that occurred
            correlation_id: Correlation ID for tracking
            error_context: Platform-specific error context

        Returns:
            Standardized error response dictionary
        """
        # Determine error type
        error_type = self._categorize_exception(exc)

        # Create error response
        error_response = ErrorResponse(
            status_code=self._get_status_code(error_type),
            error_type=error_type,
            message=str(exc) or self.default_error_message,
            detail=self._get_error_detail(exc),
            correlation_id=correlation_id,
            timestamp=self._get_timestamp(),
        )

        # Add validation errors if applicable
        if isinstance(exc, ValidationError):
            error_response.errors = self._extract_validation_errors(exc)

        # Log the error
        self._log_error(exc, error_response, correlation_id, error_context)

        return error_response.model_dump()

    def _handle_exception_group(
        self, exc: ExceptionGroup, correlation_id: str, error_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle exception groups by extracting the most relevant exception.

        Args:
            exc: The ExceptionGroup that occurred
            correlation_id: Correlation ID for tracking
            error_context: Platform-specific error context

        Returns:
            Standardized error response dictionary
        """
        # Check if this is actually an ExceptionGroup with exceptions attribute
        if not hasattr(exc, "exceptions") or not exc.exceptions:
            # Fall back to generic handling if no exceptions attribute
            return self._create_generic_exception_group_response(
                exc, correlation_id, error_context
            )

        # Extract and rank exceptions by priority
        validation_errors = [
            e for e in exc.exceptions if isinstance(e, ValidationError)
        ]
        business_errors = [
            e for e in exc.exceptions if isinstance(e, ValueError | TypeError)
        ]

        # Prioritize validation errors, then business errors, then fall back to internal
        if validation_errors:
            return self._handle_single_exception(
                validation_errors[0], correlation_id, error_context
            )
        if business_errors:
            return self._handle_single_exception(
                business_errors[0], correlation_id, error_context
            )
        # Fall back to generic exception group handling
        return self._create_generic_exception_group_response(
            exc, correlation_id, error_context
        )

    def _create_generic_exception_group_response(
        self, exc: Any, correlation_id: str, error_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a generic error response for exception groups when no specific
        exception can be prioritized.

        Args:
            exc: The ExceptionGroup that occurred
            correlation_id: Correlation ID for tracking
            error_context: Platform-specific error context

        Returns:
            Standardized error response dictionary
        """
        # Create error response with group context
        error_response = ErrorResponse(
            status_code=500,  # Exception groups are typically internal errors
            error_type=ErrorType.INTERNAL_ERROR,
            message="Multiple errors occurred during execution",
            detail=f"Exception group: {type(exc).__name__}",
            correlation_id=correlation_id,
            timestamp=self._get_timestamp(),
        )

        # Log the exception group
        self._log_error(exc, error_response, correlation_id, error_context)

        return error_response.model_dump()

    def _categorize_exception(self, exc: Exception) -> ErrorType:
        """
        Categorize exception into appropriate error type.

        Args:
            exc: The exception to categorize

        Returns:
            Appropriate ErrorType enum value
        """
        exc_type = type(exc)

        # Check direct type matches
        for exception_class, error_type in self.exception_mappings.items():
            if issubclass(exc_type, exception_class):
                return error_type

        # Default to internal error for unknown exceptions
        return ErrorType.INTERNAL_ERROR

    def _get_status_code(self, error_type: ErrorType) -> int:
        """
        Get appropriate HTTP status code for error type.

        Args:
            error_type: The categorized error type

        Returns:
            HTTP status code
        """
        status_code_mapping = {
            ErrorType.VALIDATION_ERROR: 422,
            ErrorType.AUTHENTICATION_ERROR: 401,
            ErrorType.AUTHORIZATION_ERROR: 403,
            ErrorType.NOT_FOUND_ERROR: 404,
            ErrorType.CONFLICT_ERROR: 409,
            ErrorType.BUSINESS_RULE_ERROR: 400,
            ErrorType.TIMEOUT_ERROR: 408,
            ErrorType.INTERNAL_ERROR: 500,
        }

        return status_code_mapping.get(error_type, 500)

    def _get_error_detail(self, exc: Exception) -> str:
        """
        Get detailed error information.

        Args:
            exc: The exception that occurred

        Returns:
            Detailed error description
        """
        if self.expose_internal_details:
            return f"{type(exc).__name__}: {exc!s}"
        return str(exc) or "An unexpected error occurred"

    def _extract_validation_errors(self, exc: ValidationError) -> list[ErrorDetail]:
        """
        Extract validation errors from Pydantic ValidationError.

        Args:
            exc: Pydantic ValidationError instance

        Returns:
            List of ErrorDetail objects
        """
        errors = []

        for error in exc.errors():
            field_name = error.get("loc", [None])[-1] if error.get("loc") else None
            field = field_name if isinstance(field_name, str) else None

            error_detail = ErrorDetail(
                field=field,
                code=error.get("type", "validation_error"),
                message=error.get("msg", "Validation failed"),
                context={"input": error.get("input")} if error.get("input") else None,
            )
            errors.append(error_detail)

        return errors

    def _get_timestamp(self) -> datetime:
        """
        Get current timestamp.

        Returns:
            Current datetime object
        """
        return datetime.now(UTC)

    def _log_error(
        self,
        exc: Exception,
        error_response: ErrorResponse,
        correlation_id: str,
        error_context: dict[str, Any],
    ) -> None:
        """
        Log error information using structured logging.

        Args:
            exc: The exception that occurred
            error_response: The generated error response
            correlation_id: Correlation ID for tracking
            error_context: Platform-specific error context
        """
        # Prepare log data with platform-specific context information
        log_data = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "error_type": error_response.error_type,
            "status_code": error_response.status_code,
            "correlation_id": correlation_id,
            "stack_trace": traceback.format_exc() if self.include_stack_trace else None,
        }

        # Add platform-specific context information
        log_data.update(error_context)

        # Log to structured logger
        self.structured_logger.error(
            "Exception occurred during request processing", **log_data
        )

        # Also log to standard logger for backward compatibility
        self.standard_logger.error(
            f"Exception in {self.name}: {type(exc).__name__}: {exc!s}",
            extra={
                "correlation_id": correlation_id,
                "error_type": error_response.error_type,
                "status_code": error_response.status_code,
                "function_name": error_context.get("function_name"),
                "request_id": error_context.get("request_id"),
            },
        )

    def get_error_context(self, request_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Get error context from request data.

        Args:
            request_data: The request data dictionary

        Returns:
            Error context if available, None otherwise
        """
        return request_data.get("_error_context")


# Convenience function for creating exception handler middleware
def create_exception_handler_middleware(
    *,
    strategy: ErrorHandlingStrategy,
    name: str | None = None,
    logger_name: str = "exception_handler",
    include_stack_trace: bool = False,
    expose_internal_details: bool = False,
    default_error_message: str = "An error occurred while processing your request",
) -> ExceptionHandlerMiddleware:
    """
    Create exception handler middleware with common configuration.

    Args:
        strategy: The error handling strategy to use
        name: Optional middleware name
        logger_name: Name for error logger instance
        include_stack_trace: Whether to include stack traces in error responses
        expose_internal_details: Whether to expose internal error details to clients
        default_error_message: Default message for unhandled errors

    Returns:
        Configured ExceptionHandlerMiddleware instance
    """
    return ExceptionHandlerMiddleware(
        strategy=strategy,
        name=name,
        logger_name=logger_name,
        include_stack_trace=include_stack_trace,
        expose_internal_details=expose_internal_details,
        default_error_message=default_error_message,
    )


# Factory function for AWS Lambda error handling middleware
def aws_lambda_exception_handler_middleware(
    *,
    name: str | None = None,
    logger_name: str = "exception_handler",
    include_stack_trace: bool = False,
    expose_internal_details: bool = False,
    default_error_message: str = "An error occurred while processing your request",
) -> ExceptionHandlerMiddleware:
    """
    Create exception handler middleware for AWS Lambda.

    Args:
        name: Optional middleware name
        logger_name: Name for error logger instance
        include_stack_trace: Whether to include stack traces in error responses
        expose_internal_details: Whether to expose internal error details to clients
        default_error_message: Default message for unhandled errors

    Returns:
        Configured ExceptionHandlerMiddleware instance for AWS Lambda
    """
    strategy = AWSLambdaErrorHandlingStrategy()

    return create_exception_handler_middleware(
        strategy=strategy,
        name=name,
        logger_name=logger_name,
        include_stack_trace=include_stack_trace,
        expose_internal_details=expose_internal_details,
        default_error_message=default_error_message,
    )
