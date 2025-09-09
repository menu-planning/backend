"""Secure error response models using Pydantic v2 for data protection.

This module provides secure error response models that prevent internal details,
stack traces, and implementation details from leaking in error responses using
Pydantic v2 validators and field protection mechanisms.

Key Features:
    - Stack trace protection in production environments
    - Internal details filtering and sanitization
    - Secure error response creation with BaseApiModel patterns
    - Production vs development mode configuration
    - Comprehensive data protection using Pydantic validators

Security Features:
    - Automatic stack trace removal in production
    - Internal implementation detail filtering
    - Sensitive data pattern detection and removal
    - Environment-aware security configuration
    - Pydantic v2 field validation for data protection
"""

import os
import re
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel
from src.contexts.seedwork.adapters.api_schemas.validators import sanitize_text_input


def protect_stack_traces(v: str | None) -> str | None:
    """Protect stack traces from leaking in production error responses.

    This validator removes or sanitizes stack trace information when running
    in production environments to prevent internal implementation details
    from being exposed to clients.

    Args:
        v: Text that may contain stack trace information

    Returns:
        Text with stack traces removed or sanitized based on environment
    """
    if v is None:
        return None

    # First apply standard sanitization
    sanitized = sanitize_text_input(v)
    if sanitized is None:
        return None

    # Check if we're in production mode
    is_production = os.getenv("ENVIRONMENT", "development").lower() in [
        "production",
        "prod",
    ]

    if is_production:
        # Stack trace patterns to remove in production
        stack_trace_patterns = [
            r"Traceback \(most recent call last\):",
            r"File \"[^\"]+\", line \d+, in .+",
            r"  File \"[^\"]+\", line \d+, in .+",
            r"    .+",
            r"raise .+",
            r"Exception: .+",
            r"Error: .+",
            r"at 0x[0-9a-fA-F]+",
            r"built-in",
            r"<module>",
            r"<lambda>",
            r"<listcomp>",
            r"<dictcomp>",
            r"<setcomp>",
            r"<genexpr>",
        ]

        for pattern in stack_trace_patterns:
            sanitized = re.sub(
                pattern, "[STACK_TRACE_REDACTED]", sanitized, flags=re.MULTILINE
            )

    return sanitized.strip() if sanitized.strip() else None


def protect_internal_details(v: str | None) -> str | None:
    """Protect internal implementation details from leaking in error responses.

    This validator removes internal paths, implementation details, and
    system-specific information that could be useful to attackers.

    Args:
        v: Text that may contain internal details

    Returns:
        Text with internal details removed or sanitized
    """
    if v is None:
        return None

    # First apply standard sanitization
    sanitized = sanitize_text_input(v)
    if sanitized is None:
        return None

    # Internal detail patterns to remove
    internal_patterns = [
        # File system paths
        r"/src/",
        r"/home/[^/]+/",
        r"/var/",
        r"C:\\",
        r"D:\\",
        r"E:\\",
        # Internal service names
        r"ExceptionHandlerMiddleware",
        r"AWSLambdaErrorHandlingStrategy",
        r"error_handling",
        r"middleware",
        r"adapters",
        r"services",
        r"domain",
        # Internal class names and methods
        r"<class '[^']+'>",
        r"<function [^>]+>",
        r"<method [^>]+>",
        r"<bound method [^>]+>",
        # Database and connection details
        r"connection_id: \d+",
        r"session_id: [a-f0-9-]+",
        r"transaction_id: [a-f0-9-]+",
        # Internal error codes
        r"internal_error_code: \d+",
        r"debug_id: [a-f0-9-]+",
    ]

    for pattern in internal_patterns:
        sanitized = re.sub(
            pattern, "[INTERNAL_DETAIL_REDACTED]", sanitized, flags=re.IGNORECASE
        )

    return sanitized.strip() if sanitized.strip() else None


def validate_error_type(v: str) -> str:
    """Validate and sanitize error type to ensure it's safe for client consumption.

    This validator ensures error types are safe and don't contain sensitive
    information or malicious content.

    Args:
        v: Error type string to validate

    Returns:
        Sanitized and validated error type
    """
    if not v:
        return "internal_error"

    # Apply standard sanitization
    sanitized = sanitize_text_input(v)
    if not sanitized:
        return "internal_error"

    # Ensure error type is safe (alphanumeric and underscores only)
    safe_error_type = re.sub(r"[^a-zA-Z0-9_]", "_", sanitized)

    # Limit length to prevent abuse
    if len(safe_error_type) > 50:
        safe_error_type = safe_error_type[:50]

    return safe_error_type.lower()


# Custom field types with data protection
ProtectedText = Annotated[str, BeforeValidator(protect_internal_details)]
StackTraceProtectedText = Annotated[str, BeforeValidator(protect_stack_traces)]
SafeErrorType = Annotated[str, BeforeValidator(validate_error_type)]


class SecureErrorDetail(BaseModel):
    """Secure error detail with comprehensive data protection.

    This model provides secure error details that automatically protect
    against sensitive data leakage and internal detail exposure.

    Security Features:
        - Internal detail protection
        - Stack trace protection in production
        - Safe error type validation
        - Comprehensive text sanitization
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: ProtectedText | None = Field(
        default=None, description="Field name if error is field-specific (protected)"
    )
    code: SafeErrorType = Field(
        ..., description="Error code for programmatic handling (validated)"
    )
    message: StackTraceProtectedText = Field(
        ..., description="Human-readable error message (stack trace protected)"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Additional error context (sanitized)"
    )

    @field_validator("context")
    @classmethod
    def sanitize_context(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Sanitize context dictionary values to prevent sensitive data leakage.

        Args:
            v: Context dictionary to sanitize

        Returns:
            Sanitized context dictionary
        """
        if v is None:
            return None

        sanitized_context = {}
        for key, value in v.items():
            if isinstance(value, str):
                # Apply both internal detail protection and standard sanitization
                protected_value = protect_internal_details(value)
                sanitized_context[key] = protected_value
            else:
                sanitized_context[key] = value

        return sanitized_context


class SecureErrorResponse(BaseApiModel):
    """Secure error response model with comprehensive data protection.

    This model provides secure error responses that automatically protect
    against sensitive data leakage, stack trace exposure, and internal
    detail revelation using Pydantic v2 validators.

    Security Features:
        - Stack trace protection in production environments
        - Internal detail filtering and sanitization
        - Safe error type validation
        - Comprehensive text sanitization
        - Environment-aware security configuration
    """

    # Core error fields with comprehensive protection
    status_code: int = Field(..., description="HTTP status code", ge=400, le=599)
    error_type: SafeErrorType = Field(
        ..., description="Categorized error type (validated)"
    )
    message: StackTraceProtectedText = Field(
        ..., description="High-level error message (protected)"
    )
    detail: ProtectedText = Field(
        ..., description="Detailed error description (protected)"
    )
    errors: list[SecureErrorDetail] | None = Field(
        default=None,
        description="Specific error details for validation errors (protected)",
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Additional error context (sanitized)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the error occurred (ISO format)",
    )
    correlation_id: ProtectedText | None = Field(
        default=None, description="Request correlation ID for tracking (protected)"
    )

    @field_validator("context")
    @classmethod
    def sanitize_context(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Sanitize context dictionary values to prevent sensitive data leakage.

        Args:
            v: Context dictionary to sanitize

        Returns:
            Sanitized context dictionary
        """
        if v is None:
            return None

        sanitized_context = {}
        for key, value in v.items():
            if isinstance(value, str):
                # Apply both internal detail protection and standard sanitization
                protected_value = protect_internal_details(value)
                sanitized_context[key] = protected_value
            else:
                sanitized_context[key] = value

        return sanitized_context

    @field_validator("status_code")
    @classmethod
    def validate_status_code(cls, v: int) -> int:
        """Validate status code is within acceptable error range.

        Args:
            v: Status code to validate

        Returns:
            Validated status code

        Raises:
            ValueError: If status code is not in error range (400-599)
        """
        if not (400 <= v <= 599):
            raise ValueError(
                "Status code must be between 400 and 599 for error responses"
            )
        return v


class ProductionSecurityConfig(BaseModel):
    """Production security configuration for error responses.

    This model provides configuration options for controlling
    security features in different environments.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_stack_trace_protection: bool = Field(
        default=True, description="Enable stack trace protection in production"
    )
    enable_internal_detail_protection: bool = Field(
        default=True, description="Enable internal detail protection"
    )
    enable_sensitive_data_sanitization: bool = Field(
        default=True, description="Enable sensitive data sanitization"
    )
    max_error_message_length: int = Field(
        default=500, description="Maximum length for error messages"
    )
    max_detail_length: int = Field(
        default=1000, description="Maximum length for error details"
    )

    @classmethod
    def for_environment(
        cls, environment: str = "development"
    ) -> "ProductionSecurityConfig":
        """Create security configuration based on environment.

        Args:
            environment: Environment name (development, staging, production)

        Returns:
            Security configuration appropriate for the environment
        """
        is_production = environment.lower() in ["production", "prod"]

        return cls(
            enable_stack_trace_protection=is_production,
            enable_internal_detail_protection=True,  # Always enabled
            enable_sensitive_data_sanitization=True,  # Always enabled
            max_error_message_length=500 if is_production else 2000,
            max_detail_length=1000 if is_production else 5000,
        )
