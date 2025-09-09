"""Exception handler middleware for consistent error responses and logging.

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
from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.contexts.shared_kernel.middleware.error_handling.error_response import (
    ErrorDetail,
    ErrorResponse,
    ErrorType,
)
from src.contexts.shared_kernel.middleware.error_handling.secure_models import (
    ProductionSecurityConfig,
    SecureErrorResponse,
)
from src.logging.logger import StructlogFactory, correlation_id_ctx


class ErrorHandlingStrategy(ABC):
    """Abstract base class for error handling strategies.

    This interface defines how different platforms (AWS Lambda, FastAPI, etc.)
    should implement error context extraction and request data handling.

    Notes:
        All methods must be implemented by concrete strategy classes.
        Platform-specific implementations handle different request formats.
    """

    @abstractmethod
    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract error context from the request.

        Args:
            *args: Positional arguments from the middleware call.
            **kwargs: Keyword arguments from the middleware call.

        Returns:
            Dictionary with error context information.
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
    def inject_error_context(
        self, request_data: dict[str, Any], error_context: dict[str, Any]
    ) -> None:
        """Inject error context into the request data.

        Args:
            request_data: The request data to modify.
            error_context: The error context to inject.
        """


class AWSLambdaErrorHandlingStrategy(ErrorHandlingStrategy):
    """AWS Lambda-specific error handling strategy.

    Extracts error context from AWS Lambda events and context objects.

    Notes:
        Handles AWS Lambda event and context objects specifically.
        Extracts function metadata and request information.
    """

    def extract_error_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Extract error context from AWS Lambda event and context.

        Args:
            *args: Positional arguments (event, context).
            **kwargs: Keyword arguments (event, context).

        Returns:
            Dictionary with error context information.
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

        Raises:
            ValueError: If event or context is missing
        """
        event: dict[str, Any] | None = (
            kwargs.get("event") if "event" in kwargs else args[0] if args else None
        )
        context: Any = (
            kwargs.get("context")
            if "context" in kwargs
            else args[1] if len(args) > 1 else None
        )

        if not event or not context:
            error_message = (
                "Event and context are required for AWS Lambda error handling"
            )
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
    """Generic exception handler middleware that uses composition for different strategies.

    Provides simple, consistent error handling across different platforms while
    maintaining the composable architecture. It delegates platform-specific
    error handling logic to strategy objects.

    Attributes:
        strategy: The error handling strategy to use.
        logger: Logger instance for error handling.
        include_stack_trace: Whether to include stack traces in error responses.
        expose_internal_details: Whether to expose internal error details to clients.
        default_error_message: Default message for unhandled errors.
        exception_mappings: Dictionary mapping exception types to error types.

    Notes:
        Order: runs last in middleware chain (catches all errors).
        Propagates cancellation: Yes.
        Adds headers: Error context.
        Retries: None; Timeout: none (handles timeouts).
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
        """Initialize exception handler middleware.

        Args:
            strategy: The error handling strategy to use.
            name: Optional name for the middleware.
            logger_name: Name for error logger instance.
            include_stack_trace: Whether to include stack traces in error responses.
            expose_internal_details: Whether to expose internal error details to clients.
            default_error_message: Default message for unhandled errors.
        """
        super().__init__(name)

        # Ensure structlog is configured
        StructlogFactory.configure()

        self.strategy = strategy
        self.logger = StructlogFactory.get_logger(logger_name)
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

        # Security configuration for data protection
        self.security_config = ProductionSecurityConfig.for_environment()

    def _create_secure_error_response(
        self,
        status_code: int,
        error_type: ErrorType,
        message: str,
        detail: str,
        correlation_id: str | None = None,
        validation_errors: list[ErrorDetail] | None = None,
        context: dict[str, Any] | None = None,
    ) -> SecureErrorResponse:
        """Create a secure error response with comprehensive data protection.

        This method creates a SecureErrorResponse instance with enhanced
        security protection using the secure models.

        Args:
            status_code: HTTP status code for the error
            error_type: Categorized error type
            message: High-level error message
            detail: Detailed error description
            correlation_id: Request correlation ID for tracking
            validation_errors: List of validation error details
            context: Additional error context

        Returns:
            SecureErrorResponse with comprehensive data protection
        """
        # Convert ErrorDetail instances to SecureErrorDetail
        secure_errors = None
        if validation_errors:
            from src.contexts.shared_kernel.middleware.error_handling.secure_models import (
                SecureErrorDetail,
            )

            secure_errors = []
            for error in validation_errors:
                secure_errors.append(
                    SecureErrorDetail(
                        field=error.field,
                        code=error.code,
                        message=error.message,
                        context=error.context,
                    )
                )

        # Apply enhanced sanitization to message and detail
        from src.contexts.shared_kernel.middleware.error_handling.error_response import (
            sanitize_error_text,
        )

        sanitized_message = sanitize_error_text(message)
        sanitized_detail = sanitize_error_text(detail)

        return SecureErrorResponse(
            status_code=status_code,
            error_type=error_type.value,
            message=sanitized_message or message,
            detail=sanitized_detail or detail,
            errors=secure_errors,
            context=context,
            timestamp=datetime.now(UTC).isoformat(),
            correlation_id=correlation_id,
        )

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute exception handler middleware around the handler.

        Args:
            handler: The next handler in the middleware chain.
            *args: Positional arguments passed to the middleware.
            **kwargs: Keyword arguments passed to the middleware.

        Returns:
            Either successful response from handler or standardized error response.

        Notes:
            Catches all exceptions and converts to standardized error responses.
            Logs successful requests at debug level for observability.
        """
        correlation_id = correlation_id_ctx.get() or "unknown"

        try:
            result = await handler(*args, **kwargs)

            # Log successful request completion at debug level for observability
            self.logger.debug(
                "Request processed successfully",
                middleware_name=self.name or "exception_handler",
                handler_name=getattr(handler, "__name__", "unknown_handler"),
            )

            return result

        except ExceptionGroup as exc:
            # Handle exception groups with proper extraction
            error_context = self.strategy.extract_error_context(*args, **kwargs)
            return self._handle_exception_group(exc, correlation_id, error_context)

        except Exception as exc:
            # Handle single exceptions
            error_context = self.strategy.extract_error_context(*args, **kwargs)
            return self._handle_single_exception(exc, correlation_id, error_context)

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

        # Extract validation errors if applicable
        validation_errors = None
        if isinstance(exc, ValidationError):
            validation_errors = self._extract_validation_errors(exc)

        # Create secure error response with data protection
        secure_error_response = self._create_secure_error_response(
            status_code=self._get_status_code(error_type),
            error_type=error_type,
            message=str(exc) or self.default_error_message,
            detail=self._get_error_detail(exc),
            correlation_id=correlation_id,
            validation_errors=validation_errors,
        )

        # Create legacy ErrorResponse for backward compatibility
        error_response = ErrorResponse(
            status_code=self._get_status_code(error_type),
            error_type=error_type,
            message=str(exc) or self.default_error_message,
            detail=self._get_error_detail(exc),
            correlation_id=correlation_id,
            timestamp=self._get_timestamp(),
            errors=validation_errors,
        )

        # Log the error
        self._log_error(exc, error_response, correlation_id, error_context)

        # Serialize secure error response for AWS Lambda format
        response_data = secure_error_response.model_dump()
        security_headers = error_response.security_headers.to_headers_dict()

        # Format for AWS Lambda response structure
        return {
            "statusCode": secure_error_response.status_code,
            "headers": security_headers,
            "body": response_data,
        }

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
        # ExceptionGroup should always have exceptions (empty groups raise ValueError)

        # Log exception group composition for debugging
        exception_types = [type(e).__name__ for e in exc.exceptions]
        self.logger.debug(
            "Processing exception group",
            exception_count=len(exc.exceptions),
            exception_types=exception_types,
            middleware_name=self.name or "exception_handler",
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
        # Create secure error response with group context
        secure_error_response = self._create_secure_error_response(
            status_code=500,  # Exception groups are typically internal errors
            error_type=ErrorType.INTERNAL_ERROR,
            message="Multiple errors occurred during execution",
            detail=f"Exception group: {type(exc).__name__}",
            correlation_id=correlation_id,
        )

        # Create legacy ErrorResponse for backward compatibility
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

        # Serialize secure error response for AWS Lambda format
        response_data = secure_error_response.model_dump()
        security_headers = error_response.security_headers.to_headers_dict()

        # Format for AWS Lambda response structure
        return {
            "statusCode": secure_error_response.status_code,
            "headers": security_headers,
            "body": response_data,
        }

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
        # Determine log level based on error severity
        is_client_error = error_response.status_code < 500
        log_level = "warning" if is_client_error else "error"

        # Prepare structured log data
        log_data = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc) or "No message provided",
            "error_type": error_response.error_type.value,
            "status_code": error_response.status_code,
            "middleware_name": self.name or "exception_handler",
        }

        # Add stack trace for server errors or when explicitly requested
        if not is_client_error or self.include_stack_trace:
            log_data["stack_trace"] = traceback.format_exc()

        # Add platform-specific context (AWS Lambda, etc.)
        if error_context:
            log_data["platform_context"] = error_context

        # Add validation error details for better debugging
        if hasattr(error_response, "errors") and error_response.errors:
            log_data["validation_errors"] = [
                {
                    "field": err.field,
                    "code": err.code,
                    "message": err.message,
                }
                for err in error_response.errors
            ]

        # Create appropriate log message based on error type
        if is_client_error:
            message = f"Client error handled: {type(exc).__name__}"
        else:
            message = f"Server error occurred: {type(exc).__name__}"

        # Log with appropriate level
        getattr(self.logger, log_level)(message, **log_data)

    def get_error_context(self, request_data: dict[str, Any]) -> dict[str, Any] | None:
        """Get error context from request data.

        Args:
            request_data: The request data dictionary.

        Returns:
            Error context if available, None otherwise.
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
    """Create exception handler middleware with common configuration.

    Args:
        strategy: The error handling strategy to use.
        name: Optional middleware name.
        logger_name: Name for error logger instance.
        include_stack_trace: Whether to include stack traces in error responses.
        expose_internal_details: Whether to expose internal error details to clients.
        default_error_message: Default message for unhandled errors.

    Returns:
        Configured ExceptionHandlerMiddleware instance.

    Notes:
        Creates ExceptionHandlerMiddleware with specified configuration.
        Provides a convenient factory function for common error handling setups.
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
    """Create exception handler middleware for AWS Lambda.

    Args:
        name: Optional middleware name.
        logger_name: Name for error logger instance.
        include_stack_trace: Whether to include stack traces in error responses.
        expose_internal_details: Whether to expose internal error details to clients.
        default_error_message: Default message for unhandled errors.

    Returns:
        Configured ExceptionHandlerMiddleware instance for AWS Lambda.

    Notes:
        Uses AWSLambdaErrorHandlingStrategy for AWS Lambda-specific error handling.
        Provides a convenient factory function for AWS Lambda error handling.
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
