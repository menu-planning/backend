"""
Error middleware for consistent exception handling and error responses.

This middleware provides standardized error handling across all endpoints by:
- Catching and categorizing all unhandled exceptions
- Converting exceptions to standardized error response schemas
- Integration with logging middleware for correlation ID tracking
- Maintaining backward compatibility with existing lambda_exception_handler patterns
- Structured error logging for observability and debugging
"""

import traceback
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from pydantic import ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.responses.error_response import (
    ErrorDetail,
    ErrorResponse,
    ErrorType,
    ValidationErrorResponse,
)
from src.logging.logger import StructlogFactory, correlation_id_ctx
from src.logging.logger import logger as standard_logger


class ErrorMiddleware:
    """
    Middleware for standardized exception handling and error response generation.

    Features:
    - Automatic exception catching and categorization
    - Standardized error response schemas
    - Correlation ID integration for error tracking
    - Backward compatibility with existing error patterns
    - Structured error logging with context
    - Configurable error detail exposure for different environments
    """

    def __init__(
        self,
        logger_name: str = "error_handler",
        include_stack_trace: bool = False,
        expose_internal_details: bool = False,
        default_error_message: str = "An error occurred while processing your request",
    ):
        """
        Initialize error middleware.

        Args:
            logger_name: Name for error logger instance
            include_stack_trace: Whether to include stack traces in error
                responses (dev only)
            expose_internal_details: Whether to expose internal error details to clients
            default_error_message: Default message for unhandled errors
        """
        # Ensure structlog is configured
        StructlogFactory.configure()

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
        handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute error middleware around endpoint handler.

        Args:
            handler: The endpoint handler function to wrap
            event: AWS Lambda event dictionary

        Returns:
            Either successful response from handler or standardized error response
        """
        correlation_id = correlation_id_ctx.get() or "unknown"

        try:
            # Execute the handler and return successful response
            response = await handler(event)
            return response

        except Exception as e:
            # Handle all exceptions and convert to standardized error responses
            return await self._handle_exception(e, event, correlation_id)

    async def _handle_exception(
        self, exception: Exception, event: dict[str, Any], correlation_id: str
    ) -> dict[str, Any]:
        """
        Handle exception and generate standardized error response.

        Args:
            exception: The caught exception
            event: Original AWS Lambda event
            correlation_id: Current request correlation ID

        Returns:
            Standardized error response dictionary
        """
        # Determine error categorization
        error_type = self._categorize_exception(exception)
        status_code = self._get_status_code_for_error_type(error_type)

        # Extract error details based on exception type
        error_response = await self._create_error_response(
            exception, error_type, status_code, correlation_id
        )

        # Log the error with context
        await self._log_error(exception, error_response, event, correlation_id)

        # Return AWS Lambda compatible response
        return {
            "statusCode": error_response.status_code,
            "headers": self._get_error_headers(),
            "body": error_response.model_dump_json(),
        }

    def _categorize_exception(self, exception: Exception) -> ErrorType:
        """
        Categorize exception type for appropriate error response.

        Args:
            exception: The exception to categorize

        Returns:
            Appropriate ErrorType for the exception
        """
        # Check for specific exception types
        exception_type = type(exception)

        # Direct mapping from exception types
        if exception_type in self.exception_mappings:
            return self.exception_mappings[exception_type]

        # Check exception message patterns for business logic categorization
        error_message = str(exception).lower()

        not_found_keywords = ["not found", "does not exist", "missing"]
        auth_keywords = ["unauthorized", "not authenticated", "invalid token"]
        authz_keywords = ["forbidden", "permission", "not allowed", "access denied"]
        conflict_keywords = ["already exists", "duplicate", "conflict"]
        timeout_keywords = ["timeout", "timed out", "connection"]
        validation_keywords = ["validation", "invalid", "required", "format"]

        if any(keyword in error_message for keyword in not_found_keywords):
            return ErrorType.NOT_FOUND_ERROR
        if any(keyword in error_message for keyword in auth_keywords):
            return ErrorType.AUTHENTICATION_ERROR
        if any(keyword in error_message for keyword in authz_keywords):
            return ErrorType.AUTHORIZATION_ERROR
        if any(keyword in error_message for keyword in conflict_keywords):
            return ErrorType.CONFLICT_ERROR
        if any(keyword in error_message for keyword in timeout_keywords):
            return ErrorType.TIMEOUT_ERROR
        if any(keyword in error_message for keyword in validation_keywords):
            return ErrorType.VALIDATION_ERROR

        # Default to internal error for unhandled cases
        return ErrorType.INTERNAL_ERROR

    def _get_status_code_for_error_type(self, error_type: ErrorType) -> int:
        """
        Map error type to appropriate HTTP status code.

        Args:
            error_type: The categorized error type

        Returns:
            HTTP status code for the error type
        """
        status_mapping = {
            ErrorType.VALIDATION_ERROR: 422,
            ErrorType.AUTHENTICATION_ERROR: 401,
            ErrorType.AUTHORIZATION_ERROR: 403,
            ErrorType.NOT_FOUND_ERROR: 404,
            ErrorType.CONFLICT_ERROR: 409,
            ErrorType.BUSINESS_RULE_ERROR: 400,
            ErrorType.TIMEOUT_ERROR: 408,
            ErrorType.INTERNAL_ERROR: 500,
        }
        return status_mapping.get(error_type, 500)

    async def _create_error_response(
        self,
        exception: Exception,
        error_type: ErrorType,
        status_code: int,
        correlation_id: str,
    ) -> ErrorResponse:
        """
        Create standardized error response from exception.

        Args:
            exception: The caught exception
            error_type: Categorized error type
            status_code: HTTP status code
            correlation_id: Request correlation ID

        Returns:
            Structured error response
        """
        # Handle Pydantic validation errors specially
        if isinstance(exception, ValidationError):
            return await self._create_validation_error_response(
                exception, correlation_id
            )

        # Determine message and detail based on exposure settings
        if self.expose_internal_details:
            message = str(exception)
            detail = str(exception)
        else:
            message = self.default_error_message
            detail = self._get_safe_error_detail(exception, error_type)

        # Add context for development
        context = None
        if self.include_stack_trace:
            context = {
                "exception_type": type(exception).__name__,
                "stack_trace": traceback.format_exc(),
            }

        return ErrorResponse(
            status_code=status_code,
            error_type=error_type,
            message=message,
            detail=detail,
            context=context,
            correlation_id=correlation_id,
        )

    async def _create_validation_error_response(
        self, validation_error: ValidationError, correlation_id: str
    ) -> ValidationErrorResponse:
        """
        Create detailed validation error response from Pydantic ValidationError.

        Args:
            validation_error: Pydantic validation error
            correlation_id: Request correlation ID

        Returns:
            Detailed validation error response
        """
        error_details = []

        for error in validation_error.errors():
            field_path = (
                ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
            )

            error_details.append(
                ErrorDetail(
                    field=field_path,
                    code=error["type"],
                    message=error["msg"],
                    context=error.get("ctx"),
                )
            )

        return ValidationErrorResponse(
            message="Validation failed",
            detail=f"Request data validation failed with {len(error_details)} error(s)",
            errors=error_details,
            correlation_id=correlation_id,
        )

    def _get_safe_error_detail(
        self, exception: Exception, error_type: ErrorType
    ) -> str:
        """
        Get safe error detail that doesn't expose internal information.

        Args:
            exception: The exception
            error_type: Categorized error type

        Returns:
            Safe error detail message
        """
        safe_messages = {
            ErrorType.VALIDATION_ERROR: "The request data is invalid or incomplete",
            ErrorType.AUTHENTICATION_ERROR: "Authentication is required",
            ErrorType.AUTHORIZATION_ERROR: (
                "You don't have permission to perform this action"
            ),
            ErrorType.NOT_FOUND_ERROR: "The requested resource was not found",
            ErrorType.CONFLICT_ERROR: "The request conflicts with the current state",
            ErrorType.BUSINESS_RULE_ERROR: "The request violates business rules",
            ErrorType.TIMEOUT_ERROR: "The request timed out",
            ErrorType.INTERNAL_ERROR: "An internal server error occurred",
        }
        return safe_messages.get(error_type, self.default_error_message)

    async def _log_error(
        self,
        exception: Exception,
        error_response: ErrorResponse,
        event: dict[str, Any],
        correlation_id: str,
    ) -> None:
        """
        Log error with structured context for observability.

        Args:
            exception: The caught exception
            error_response: Generated error response
            event: AWS Lambda event
            correlation_id: Request correlation ID
        """
        # Extract request context for logging
        request_context = {
            "method": event.get("httpMethod", "unknown"),
            "path": event.get("path", "unknown"),
            "correlation_id": correlation_id,
            "error_type": error_response.error_type.value,
            "status_code": error_response.status_code,
            "exception_type": type(exception).__name__,
        }

        # Include user context if available
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            authorizer = event["requestContext"]["authorizer"]
            if "user_id" in authorizer:
                request_context["user_id"] = authorizer["user_id"]

        # Log based on severity
        if error_response.status_code >= 500:
            # Server errors - log with full context including stack trace
            self.structured_logger.error(
                "Internal server error occurred",
                **request_context,
                exception_message=str(exception),
                stack_trace=traceback.format_exc(),
            )
        elif error_response.status_code >= 400:
            # Client errors - log with basic context
            self.structured_logger.warning(
                "Client error occurred",
                **request_context,
                exception_message=str(exception),
            )
        else:
            # Unexpected status code
            self.structured_logger.info(
                "Unexpected error response",
                **request_context,
                exception_message=str(exception),
            )

    def _get_error_headers(self) -> dict[str, str]:
        """
        Get standard headers for error responses.

        Returns:
            Dictionary of headers to include in error responses
        """
        return {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": (
                "Content-Type,X-Amz-Date,Authorization,"
                "X-Api-Key,X-Amz-Security-Token"
            ),
            "Access-Control-Allow-Methods": "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT",
        }

    @asynccontextmanager
    async def error_context(self, operation_name: str = "operation"):
        """
        Context manager for manual error handling in specific code blocks.

        Usage:
            async with error_middleware.error_context("database_operation"):
                # Code that might raise exceptions
                result = await database.query()

        Args:
            operation_name: Name of the operation for logging context
        """
        correlation_id = correlation_id_ctx.get() or "unknown"

        try:
            yield
        except Exception as e:
            # Log the error with operation context
            self.structured_logger.error(
                f"Error in {operation_name}",
                correlation_id=correlation_id,
                operation=operation_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
                stack_trace=(
                    traceback.format_exc() if self.include_stack_trace else None
                ),
            )
            # Re-raise to be handled by main middleware
            raise


# Factory functions for different error middleware configurations


def create_error_middleware(
    include_stack_trace: bool = False, expose_internal_details: bool = False
) -> ErrorMiddleware:
    """
    Create error middleware with standard configuration.

    Args:
        include_stack_trace: Whether to include stack traces (development only)
        expose_internal_details: Whether to expose internal error details

    Returns:
        Configured ErrorMiddleware instance
    """
    return ErrorMiddleware(
        include_stack_trace=include_stack_trace,
        expose_internal_details=expose_internal_details,
    )


def development_error_middleware() -> ErrorMiddleware:
    """
    Create error middleware for development environment with full error details.

    Returns:
        Development-configured ErrorMiddleware instance
    """
    return ErrorMiddleware(
        include_stack_trace=True,
        expose_internal_details=True,
        default_error_message="Development: See error details",
    )


def production_error_middleware() -> ErrorMiddleware:
    """
    Create error middleware for production environment with minimal error exposure.

    Returns:
        Production-configured ErrorMiddleware instance
    """
    return ErrorMiddleware(
        include_stack_trace=False,
        expose_internal_details=False,
        default_error_message="An error occurred while processing your request",
    )


def legacy_compatible_error_middleware() -> ErrorMiddleware:
    """
    Create error middleware that maintains compatibility with existing patterns.

    This configuration ensures backward compatibility with existing
    lambda_exception_handler and IAM error patterns.

    Returns:
        Legacy-compatible ErrorMiddleware instance
    """
    return ErrorMiddleware(
        include_stack_trace=False,
        expose_internal_details=True,  # Expose details for backward compatibility
        default_error_message="Request failed",
    )
