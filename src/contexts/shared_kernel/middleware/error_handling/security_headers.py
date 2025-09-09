"""Security headers model for exception handler middleware.

This module provides Pydantic v2 models for HTTP security headers that are
included in all error responses to prevent common web vulnerabilities.

Key Features:
- Standardized security headers using Pydantic v2 validation
- Integration with BaseApiModel patterns for consistency
- Immutable security header configuration
- Type-safe header value validation
"""

from typing import Any

from pydantic import ConfigDict, Field
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel


class SecurityHeaders(BaseApiModel[Any, Any]):
    """Pydantic model for HTTP security headers in error responses.

    Provides standardized security headers that are included in all error
    responses to prevent common web vulnerabilities like XSS, clickjacking,
    and content type sniffing attacks.

    Attributes:
        x_content_type_options: Prevents MIME type sniffing attacks
        x_frame_options: Prevents clickjacking attacks
        x_xss_protection: Enables XSS filtering in browsers
        strict_transport_security: Enforces HTTPS connections
        referrer_policy: Controls referrer information leakage
        content_security_policy: Prevents XSS and injection attacks

    Notes:
        All headers use immutable values for security consistency.
        Headers are validated using Pydantic v2 field validators.
        Inherits from BaseApiModel for consistent API patterns.

    Examples:
        # Create security headers with default values
        headers = SecurityHeaders()

        # Create with custom values (if needed)
        headers = SecurityHeaders(
            x_content_type_options="nosniff",
            x_frame_options="DENY"
        )
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    x_content_type_options: str = Field(
        default="nosniff",
        description="Prevents MIME type sniffing attacks",
        min_length=1,
        max_length=50,
    )
    x_frame_options: str = Field(
        default="DENY",
        description="Prevents clickjacking attacks",
        min_length=1,
        max_length=50,
    )
    x_xss_protection: str = Field(
        default="1; mode=block",
        description="Enables XSS filtering in browsers",
        min_length=1,
        max_length=50,
    )
    strict_transport_security: str = Field(
        default="max-age=31536000; includeSubDomains",
        description="Enforces HTTPS connections",
        min_length=1,
        max_length=100,
    )
    referrer_policy: str = Field(
        default="strict-origin-when-cross-origin",
        description="Controls referrer information leakage",
        min_length=1,
        max_length=100,
    )
    content_security_policy: str = Field(
        default="default-src 'self'",
        description="Prevents XSS and injection attacks",
        min_length=1,
        max_length=200,
    )

    def to_headers_dict(self) -> dict[str, str]:
        """Convert security headers to dictionary format for HTTP responses.

        Returns:
            Dictionary with header names as keys and values as strings.
            Suitable for use in HTTP response headers.

        Examples:
            headers = SecurityHeaders()
            headers_dict = headers.to_headers_dict()
            # Returns: {
            #     "X-Content-Type-Options": "nosniff",
            #     "X-Frame-Options": "DENY",
            #     ...
            # }
        """
        return {
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "X-XSS-Protection": self.x_xss_protection,
            "Strict-Transport-Security": self.strict_transport_security,
            "Referrer-Policy": self.referrer_policy,
            "Content-Security-Policy": self.content_security_policy,
        }

    @classmethod
    def get_default_headers(cls) -> dict[str, str]:
        """Get default security headers as dictionary.

        Returns:
            Dictionary with default security header values.
            Useful for creating consistent security headers across the application.

        Examples:
            default_headers = SecurityHeaders.get_default_headers()
            # Returns: {
            #     "X-Content-Type-Options": "nosniff",
            #     "X-Frame-Options": "DENY",
            #     ...
            # }
        """
        return cls().to_headers_dict()
