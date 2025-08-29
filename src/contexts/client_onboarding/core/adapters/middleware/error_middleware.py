"""
Error handling middleware for Client Onboarding Context.

Provides specialized error handling for TypeForm API errors, webhook processing
failures, and onboarding-specific business logic errors by extending
shared_kernel middleware patterns.

Features:
- Client onboarding specific exception mapping
- TypeForm API error categorization
- Webhook processing error handling
- Structured logging with onboarding context
- Integration with shared_kernel error response schemas
"""

import traceback
from contextlib import asynccontextmanager
from typing import Any

# Client onboarding specific exceptions
from src.contexts.client_onboarding.core.services.exceptions import (
    ClientOnboardingError,
    ConfigurationError,
    DatabaseOperationError,
    FormResponseProcessingError,
    OnboardingFormAccessError,
    OnboardingFormNotFoundError,
    TypeFormAPIError,
    TypeFormAuthenticationError,
    TypeFormFormNotFoundError,
    TypeFormRateLimitError,
    TypeFormWebhookError,
    WebhookPayloadError,
    WebhookSecurityError,
    WebhookSignatureError,
)
from src.contexts.shared_kernel.adapters.api_schemas.responses.error_response import (
    ErrorType,
)
from src.contexts.shared_kernel.middleware.error_middleware import ErrorMiddleware
from src.logging.logger import correlation_id_ctx

# Constants for HTTP status codes
HTTP_SERVER_ERROR = 500
HTTP_CLIENT_ERROR = 400


class ClientOnboardingErrorMiddleware(ErrorMiddleware):
    """
    Specialized error middleware for client onboarding context.

    Extends shared_kernel ErrorMiddleware with client onboarding specific
    exception handling, TypeForm API error mapping, and webhook error processing.
    """

    def __init__(
        self,
        logger_name: str = "client_onboarding_error_handler",
        *,
        include_stack_trace: bool = False,
        expose_internal_details: bool = False,
        default_error_message: str = "An error occurred during client onboarding",
    ):
        """
        Initialize client onboarding error middleware.

        Args:
            logger_name: Name for error logger instance
            include_stack_trace: Whether to include stack traces in error responses
            expose_internal_details: Whether to expose internal error details to clients
            default_error_message: Default message for unhandled onboarding errors
        """
        super().__init__(
            logger_name=logger_name,
            include_stack_trace=include_stack_trace,
            expose_internal_details=expose_internal_details,
            default_error_message=default_error_message,
        )

        # Client onboarding specific exception mappings - stored separately
        self.onboarding_exception_mappings = {
            # TypeForm API errors
            TypeFormAuthenticationError: ErrorType.AUTHENTICATION_ERROR,
            TypeFormFormNotFoundError: ErrorType.NOT_FOUND_ERROR,
            # Rate limits should trigger retry logic
            TypeFormRateLimitError: ErrorType.TIMEOUT_ERROR,
            TypeFormWebhookError: ErrorType.INTERNAL_ERROR,
            # Security and validation errors
            WebhookSecurityError: ErrorType.AUTHORIZATION_ERROR,
            WebhookSignatureError: ErrorType.AUTHORIZATION_ERROR,
            WebhookPayloadError: ErrorType.VALIDATION_ERROR,
            # Business logic errors
            OnboardingFormNotFoundError: ErrorType.NOT_FOUND_ERROR,
            OnboardingFormAccessError: ErrorType.AUTHORIZATION_ERROR,
            FormResponseProcessingError: ErrorType.BUSINESS_RULE_ERROR,
            # System errors
            DatabaseOperationError: ErrorType.INTERNAL_ERROR,
            ConfigurationError: ErrorType.INTERNAL_ERROR,
            # Base client onboarding error
            ClientOnboardingError: ErrorType.BUSINESS_RULE_ERROR,
            TypeFormAPIError: ErrorType.INTERNAL_ERROR,
        }

    def _categorize_exception(self, exception: Exception) -> ErrorType:
        """
        Categorize exception with client onboarding specific logic.

        Args:
            exception: The exception to categorize

        Returns:
            Appropriate ErrorType for the exception
        """
        # First check client onboarding specific exceptions
        exception_type = type(exception)
        if exception_type in self.onboarding_exception_mappings:
            return self.onboarding_exception_mappings[exception_type]

        # Fall back to base middleware categorization
        return super()._categorize_exception(exception)

    def _get_safe_error_detail(
        self, exception: Exception, error_type: ErrorType
    ) -> str:
        """
        Get safe error detail with client onboarding specific messages.

        Args:
            exception: The exception
            error_type: Categorized error type

        Returns:
            Safe error detail message appropriate for client onboarding
        """
        # Define error message mappings for specific exception types
        error_messages = {
            TypeFormRateLimitError: self._get_rate_limit_message,
            TypeFormAuthenticationError: lambda _: (
                "TypeForm API authentication failed. Please check your API credentials"
            ),
            TypeFormFormNotFoundError: lambda _: (
                "The requested TypeForm form could not be found or is not accessible"
            ),
            WebhookSignatureError: lambda _: (
                "Webhook signature verification failed. Invalid request source"
            ),
            OnboardingFormAccessError: lambda _: (
                "You don't have permission to access this onboarding form"
            ),
            FormResponseProcessingError: lambda e: (
                f"Form response processing failed: {e.processing_stage}"
            ),
            ConfigurationError: lambda _: (
                "Service configuration error. Please contact support"
            ),
        }

        # Check if we have a specific message for this exception type
        exception_type = type(exception)
        if exception_type in error_messages:
            return error_messages[exception_type](exception)

        # Fall back to base middleware safe messages
        return super()._get_safe_error_detail(exception, error_type)

    def _get_rate_limit_message(self, exception: TypeFormRateLimitError) -> str:
        """Get rate limit error message with retry information."""
        if exception.retry_after:
            return (
                f"TypeForm API rate limit exceeded. "
                f"Please try again in {exception.retry_after} seconds"
            )
        return "TypeForm API rate limit exceeded. Please try again later"

    async def _log_error(
        self,
        exception: Exception,
        error_response,
        event: dict[str, Any],
        correlation_id: str,
    ) -> None:
        """
        Log error with client onboarding specific context.

        Args:
            exception: The caught exception
            error_response: Generated error response
            event: AWS Lambda event
            correlation_id: Request correlation ID
        """
        # Extract base request context
        request_context = {
            "method": event.get("httpMethod", "unknown"),
            "path": event.get("path", "unknown"),
            "correlation_id": correlation_id,
            "error_type": error_response.error_type.value,
            "status_code": error_response.status_code,
            "exception_type": type(exception).__name__,
            "context": "client_onboarding",
        }

        # Add client onboarding specific context
        onboarding_context = self._extract_onboarding_context(exception, event)
        request_context.update(onboarding_context)

        # Include user context if available
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            authorizer = event["requestContext"]["authorizer"]
            if "user_id" in authorizer:
                request_context["user_id"] = authorizer["user_id"]

        # Log based on severity with onboarding context
        if error_response.status_code >= HTTP_SERVER_ERROR:
            self.structured_logger.error(
                "Client onboarding internal error",
                **request_context,
                exception_message=str(exception),
                stack_trace=traceback.format_exc(),
            )
        elif error_response.status_code >= HTTP_CLIENT_ERROR:
            self.structured_logger.warning(
                "Client onboarding client error",
                **request_context,
                exception_message=str(exception),
            )
        else:
            self.structured_logger.info(
                "Client onboarding unexpected error response",
                **request_context,
                exception_message=str(exception),
            )

    def _extract_onboarding_context(
        self, exception: Exception, _event: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract client onboarding specific context from exception and event.

        Args:
            exception: The caught exception
            _event: AWS Lambda event (unused but required for interface compatibility)

        Returns:
            Dictionary of onboarding specific context for logging
        """
        context = {}

        # TypeForm specific context
        if isinstance(exception, TypeFormAPIError):
            context["typeform_api_error"] = True
            if hasattr(exception, "status_code") and exception.status_code:
                context["typeform_status_code"] = str(exception.status_code)

        if isinstance(exception, TypeFormFormNotFoundError):
            context["typeform_form_id"] = exception.form_id

        if isinstance(exception, TypeFormRateLimitError):
            context["rate_limit_error"] = True
            if exception.retry_after:
                context["retry_after_seconds"] = str(exception.retry_after)

        # Webhook specific context
        if isinstance(exception, WebhookSecurityError):
            context["webhook_security_error"] = True

        if isinstance(exception, WebhookPayloadError):
            context["webhook_payload_error"] = True
            if hasattr(exception, "payload_issue"):
                context["payload_issue"] = exception.payload_issue

        # Form processing context
        if isinstance(exception, FormResponseProcessingError):
            context["form_processing_error"] = True
            context["processing_stage"] = exception.processing_stage
            context["response_id"] = exception.response_id

        if isinstance(exception, OnboardingFormAccessError):
            context["form_access_error"] = True
            context["target_form_id"] = str(exception.form_id)

        # Database operation context
        if isinstance(exception, DatabaseOperationError):
            context["database_error"] = True
            context["operation"] = exception.operation
            context["entity"] = exception.entity

        return context

    @asynccontextmanager
    async def onboarding_operation_context(
        self,
        operation_name: str,
        form_id: int | None = None,
        user_id: int | None = None,
    ):
        """
        Context manager for client onboarding operations with enhanced logging.

        Usage:
            async with error_middleware.onboarding_operation_context(
                "typeform_webhook_processing",
                form_id=123,
                user_id=456
            ):
                # Process webhook payload
                result = await process_webhook()

        Args:
            operation_name: Name of the onboarding operation
            form_id: Optional form ID for context
            user_id: Optional user ID for context
        """
        correlation_id = correlation_id_ctx.get() or "unknown"
        operation_context = {
            "operation": operation_name,
            "context": "client_onboarding",
            "correlation_id": correlation_id,
        }

        if form_id:
            operation_context["form_id"] = str(form_id)
        if user_id:
            operation_context["user_id"] = str(user_id)

        try:
            self.structured_logger.info(
                f"Starting client onboarding operation: {operation_name}",
                **operation_context,
            )
            yield
            self.structured_logger.info(
                f"Completed client onboarding operation: {operation_name}",
                **operation_context,
            )
        except Exception as e:
            additional_context = {
                "exception_type": type(e).__name__,
                "exception_message": str(e),
            }
            if self.include_stack_trace:
                additional_context["stack_trace"] = traceback.format_exc()

            # Update with additional context using dict comprehension
            operation_context.update(additional_context)

            self.structured_logger.exception(
                f"Error in client onboarding operation: {operation_name}",
                **operation_context,
            )
            # Re-raise to be handled by main middleware
            raise


# Factory functions for client onboarding error middleware


def create_client_onboarding_error_middleware(
    *, include_stack_trace: bool = False, expose_internal_details: bool = False
) -> ClientOnboardingErrorMiddleware:
    """
    Create client onboarding error middleware with standard configuration.

    Args:
        include_stack_trace: Whether to include stack traces (development only)
        expose_internal_details: Whether to expose internal error details

    Returns:
        Configured ClientOnboardingErrorMiddleware instance
    """
    return ClientOnboardingErrorMiddleware(
        include_stack_trace=include_stack_trace,
        expose_internal_details=expose_internal_details,
    )


def development_client_onboarding_error_middleware() -> ClientOnboardingErrorMiddleware:
    """
    Create client onboarding error middleware for development environment.

    Returns:
        Development-configured ClientOnboardingErrorMiddleware instance
    """
    return ClientOnboardingErrorMiddleware(
        include_stack_trace=True,
        expose_internal_details=True,
        default_error_message="Development: Client onboarding error details available",
    )


def production_client_onboarding_error_middleware() -> ClientOnboardingErrorMiddleware:
    """
    Create client onboarding error middleware for production environment.

    Returns:
        Production-configured ClientOnboardingErrorMiddleware instance
    """
    return ClientOnboardingErrorMiddleware(
        include_stack_trace=False,
        expose_internal_details=False,
        default_error_message="An error occurred during client onboarding",
    )
