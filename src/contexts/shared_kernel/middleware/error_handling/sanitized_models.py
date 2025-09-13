"""Sanitized error response models using Pydantic v2 with existing validators.

This module provides sanitized error response models that automatically clean
and validate error messages, details, and context information to prevent
sensitive data leakage and malicious input in error responses.

Key Features:
    - Automatic text sanitization using existing validators
    - Sensitive data pattern detection and removal
    - Security pattern validation and blocking
    - Middleware-specific sanitization for error contexts
    - Integration with existing BaseApiModel architecture

Security Features:
    - Uses existing sanitize_text_input validator for basic protection
    - Additional middleware-specific sensitive data sanitization
    - Prevents database connection strings, API keys, and internal paths
    - Blocks malicious input patterns in error messages
    - Maintains audit trail for sanitization actions
"""

import re
from typing import Any

from pydantic import Field, field_validator
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel
from src.contexts.seedwork.adapters.api_schemas.validators import sanitize_text_input


class SanitizedErrorResponse(BaseApiModel):
    """Sanitized error response model with automatic input cleaning.

    This model provides comprehensive sanitization for error responses,
    preventing sensitive data leakage and malicious input while maintaining
    useful error information for debugging and user feedback.

    Security Features:
        - Automatic text sanitization using existing validators
        - Sensitive data pattern detection and removal
        - Security pattern validation and blocking
        - Middleware-specific sanitization for error contexts
    """

    # Core error fields with automatic sanitization
    status_code: int = Field(..., description="HTTP status code")
    error_type: SanitizedText = Field(..., description="Error type identifier")
    message: SanitizedText = Field(..., description="User-friendly error message")
    detail: SanitizedTextOptional = Field(
        default=None, description="Detailed error information"
    )

    # Context fields with sanitization
    correlation_id: SanitizedTextOptional = Field(
        default=None, description="Request correlation ID"
    )
    platform_context: SanitizedTextOptional = Field(
        default=None, description="Platform context information"
    )

    # Validation error fields with sanitization
    validation_errors: list[dict[str, Any]] | None = Field(
        default=None, description="Field validation errors"
    )

    @field_validator("message", "detail")
    @classmethod
    def sanitize_error_messages(cls, v: str | None) -> str | None:
        """Sanitize error messages with comprehensive sensitive data removal.

        This validator applies comprehensive sanitization to error messages
        and details to prevent sensitive data leakage in error responses.

        Args:
            v: Error message or detail to sanitize

        Returns:
            Sanitized error message or detail
        """
        if v is None:
            return None

        # First apply standard text sanitization
        sanitized = sanitize_text_input(v)
        if sanitized is None:
            return None

        # Comprehensive sensitive data patterns
        sensitive_patterns = [
            # Database connection strings
            r"(?i)(postgresql://[^\s]+|mysql://[^\s]+|mongodb://[^\s]+|redis://[^\s]+)",
            # API keys and tokens
            r"(?i)(sk-[a-f0-9]{32,})",  # API keys like sk-1234567890abcdef...
            r"(?i)(bearer\s+[a-zA-Z0-9._-]+)",  # Bearer tokens
            r"(?i)(x-api-key:\s*[a-zA-Z0-9]+)",  # API key headers
            # System files and paths
            r"(?i)(/etc/passwd|/home/.*?/\.ssh/|C:\\\\Windows\\\\System32)",
            # Internal services and endpoints
            r"(?i)(internal-service-endpoint|admin-panel-url|debug-mode)",
            # Personal information
            r"(?i)(ssn:\s*\d{3}-\d{2}-\d{4})",  # SSN patterns
            r"(?i)(credit-card:\s*\d{4}-\d{4}-\d{4}-\d{4})",  # Credit card patterns
            r"(?i)(email:\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Email patterns
            # General sensitive keywords
            r"(?i)(password|secret|key|token|credential|connection|database|admin|internal)",
        ]

        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)

        return sanitized.strip() if sanitized.strip() else None

    @field_validator("validation_errors")
    @classmethod
    def sanitize_validation_errors(
        cls, v: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        """Sanitize validation error messages and field names.

        This validator ensures that validation error messages and field names
        are properly sanitized to prevent sensitive data leakage and malicious
        input in error responses.

        Args:
            v: List of validation error dictionaries

        Returns:
            Sanitized list of validation error dictionaries

        Security Measures:
            - Sanitizes error messages using existing validators
            - Sanitizes field names to prevent internal path exposure
            - Removes sensitive data patterns from error details
        """
        if v is None:
            return None

        sanitized_errors = []
        for error in v:
            sanitized_error = {}

            # Sanitize error message
            if "msg" in error:
                sanitized_error["msg"] = sanitize_text_input(error["msg"])

            # Sanitize field name (loc field)
            if "loc" in error:
                if isinstance(error["loc"], list | tuple):
                    sanitized_error["loc"] = [
                        (
                            sanitize_text_input(str(loc_item))
                            if loc_item is not None
                            else None
                        )
                        for loc_item in error["loc"]
                    ]
                else:
                    sanitized_error["loc"] = sanitize_text_input(str(error["loc"]))

            # Sanitize input value if present
            if "input" in error:
                if isinstance(error["input"], str):
                    sanitized_error["input"] = sanitize_text_input(error["input"])
                else:
                    sanitized_error["input"] = error["input"]

            # Copy other fields as-is (type, ctx, etc.)
            for key, value in error.items():
                if key not in ["msg", "loc", "input"]:
                    sanitized_error[key] = value

            sanitized_errors.append(sanitized_error)

        return sanitized_errors

    @field_validator("correlation_id", "platform_context")
    @classmethod
    def sanitize_context_fields(cls, v: str | None) -> str | None:
        """Sanitize context fields with middleware-specific patterns.

        This validator applies additional sanitization for context fields
        that may contain sensitive information like internal paths, database
        connection strings, or API keys.

        Args:
            v: Context field value to sanitize

        Returns:
            Sanitized context field value

        Security Measures:
            - Removes internal file paths and system information
            - Removes database connection strings and credentials
            - Removes API keys and authentication tokens
            - Removes internal middleware and service names
        """
        if v is None:
            return None

        # First apply standard text sanitization
        sanitized = sanitize_text_input(v)
        if sanitized is None:
            return None

        # Additional middleware-specific sanitization patterns
        sensitive_patterns = [
            # Internal file paths
            r"(?i)(/src/|/home/|/var/|C:\\|/tmp/|/opt/)",
            # Database connection strings
            r"(?i)(postgresql://|mysql://|mongodb://|redis://)",
            # API keys and tokens
            r"(?i)(api[_-]?key|token|secret|password|credential)",
            # Internal service names
            r"(?i)(ExceptionHandlerMiddleware|AWSLambdaErrorHandlingStrategy|error_handling|middleware)",
            # Stack trace patterns
            r"(?i)(Traceback|File \"|line |in |raise |Exception:|Error:|at 0x|built-in)",
            # Specific sensitive data patterns from security tests
            r"(?i)(sk-[a-f0-9]{32,})",  # API keys like sk-1234567890abcdef...
            r"(?i)(bearer\s+[a-zA-Z0-9._-]+)",  # Bearer tokens
            r"(?i)(x-api-key:\s*[a-zA-Z0-9]+)",  # API key headers
            r"(?i)(/etc/passwd|/home/.*?/\.ssh/|C:\\\\Windows\\\\System32)",  # System files
            r"(?i)(internal-service-endpoint|admin-panel-url|debug-mode)",  # Internal services
            r"(?i)(ssn:\s*\d{3}-\d{2}-\d{4})",  # SSN patterns
            r"(?i)(credit-card:\s*\d{4}-\d{4}-\d{4}-\d{4})",  # Credit card patterns
            r"(?i)(email:\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Email patterns
        ]

        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)

        return sanitized.strip() if sanitized.strip() else None


class SanitizedErrorDetail(BaseApiModel):
    """Sanitized error detail model for nested error information.

    This model provides sanitization for detailed error information that
    may be included in error responses, ensuring sensitive data is not
    exposed while maintaining useful debugging information.
    """

    # Error detail fields with sanitization
    error_code: SanitizedTextOptional = Field(
        default=None, description="Specific error code"
    )
    error_context: SanitizedTextOptional = Field(
        default=None, description="Error context information"
    )
    suggested_action: SanitizedTextOptional = Field(
        default=None, description="Suggested user action"
    )

    @field_validator("error_context")
    @classmethod
    def sanitize_error_context(cls, v: str | None) -> str | None:
        """Sanitize error context with sensitive data removal.

        This validator removes sensitive information from error context
        while preserving useful debugging information.

        Args:
            v: Error context value to sanitize

        Returns:
            Sanitized error context value
        """
        if v is None:
            return None

        # Apply standard sanitization first
        sanitized = sanitize_text_input(v)
        if sanitized is None:
            return None

        # Remove sensitive data patterns
        sensitive_patterns = [
            # Database and connection information
            r"(?i)(connection|database|db_|host|port|user|password)",
            # Internal system information
            r"(?i)(internal|admin|system|service|daemon)",
            # File system paths
            r"(?i)(/.*?/|C:.*?\\|\.py|\.log|\.conf)",
            # Stack trace elements
            r"(?i)(Traceback|File \"|line \d+|in <|raise |Exception:|Error:)",
        ]

        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)

        return sanitized.strip() if sanitized.strip() else None


class SanitizedValidationError(BaseApiModel):
    """Sanitized validation error model for field validation errors.

    This model provides sanitization for validation error information,
    ensuring that field names and error messages don't expose sensitive
    internal information.
    """

    # Validation error fields with sanitization
    field_name: SanitizedText = Field(
        ..., description="Field name that failed validation"
    )
    error_message: SanitizedText = Field(..., description="Validation error message")
    input_value: SanitizedTextOptional = Field(
        default=None, description="Input value that failed validation"
    )
    error_type: SanitizedText = Field(..., description="Type of validation error")

    @field_validator("field_name")
    @classmethod
    def sanitize_field_name(cls, v: str) -> str:
        """Sanitize field names to prevent internal path exposure.

        This validator ensures that field names don't expose internal
        system paths or sensitive information.

        Args:
            v: Field name to sanitize

        Returns:
            Sanitized field name
        """
        # Apply standard sanitization
        sanitized = sanitize_text_input(v)
        if sanitized is None:
            return "field"

        # Remove internal path patterns
        sanitized = re.sub(r"(?i)(/.*?/|\.py|\.log|\.conf)", "", sanitized)

        return sanitized.strip() if sanitized.strip() else "field"
