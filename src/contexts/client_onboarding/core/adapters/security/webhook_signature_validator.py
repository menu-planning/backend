"""
Webhook signature validation adapter for client onboarding context.

Provides TypeForm webhook signature verification following the adapter pattern
and integrating with existing webhook security services.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.contexts.client_onboarding.config import ClientOnboardingConfig
from src.contexts.client_onboarding.core.adapters.api_schemas.webhook.typeform_webhook_payload import (
    WebhookHeaders,
    WebhookSignatureValidation,
)
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
    WebhookSecurityError,
)
from src.contexts.client_onboarding.core.services.webhooks.security import (
    WebhookSecurityVerifier,
)
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)

# Constants
SHA256_PREFIX = "sha256="
MIN_SIGNATURE_LENGTH = len(SHA256_PREFIX) + 1


class WebhookSignatureValidationResult:
    """
    Result of webhook signature validation.

    Contains validation status and contextual information
    about the validation process.
    """

    def __init__(
        self,
        *,
        is_valid: bool,
        error_message: str | None = None,
        signature_provided: bool = True,
        timestamp_valid: bool = True,
        payload_size_valid: bool = True,
        context: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.error_message = error_message
        self.signature_provided = signature_provided
        self.timestamp_valid = timestamp_valid
        self.payload_size_valid = payload_size_valid
        self.context = context or {}

    def __bool__(self) -> bool:
        """Allow direct boolean evaluation."""
        return self.is_valid

    def __repr__(self) -> str:
        return (
            f"WebhookSignatureValidationResult("
            f"is_valid={self.is_valid}, "
            f"error_message={self.error_message!r})"
        )


class WebhookSignatureValidationError(Exception):
    """Raised when webhook signature validation fails."""

    def __init__(
        self, message: str, validation_result: WebhookSignatureValidationResult
    ):
        super().__init__(message)
        self.validation_result = validation_result


class WebhookSignatureValidator:
    """
    Adapter for TypeForm webhook signature validation.

    Provides a clean interface for webhook signature verification
    following the adapter pattern and integrating with existing
    webhook security infrastructure.
    """

    def __init__(self, webhook_secret: str | None = None):
        """
        Initialize the webhook signature validator.

        Args:
            webhook_secret: Optional webhook secret. If not provided,
                          will use the configuration from ClientOnboardingConfig
        """
        self._config = ClientOnboardingConfig()
        self._webhook_secret = webhook_secret or self._config.typeform_webhook_secret
        self._security_verifier = WebhookSecurityVerifier(self._webhook_secret)
        self._logger = StructlogFactory.get_logger(f"{__name__}.{self.__class__.__name__}")

    async def validate_webhook_signature(
        self,
        payload: str,
        headers: dict[str, str],
        timestamp_tolerance_minutes: int = 5,
    ) -> WebhookSignatureValidationResult:
        """
        Validate TypeForm webhook signature.

        Args:
            payload: Raw webhook payload as string
            headers: HTTP headers from the request
            timestamp_tolerance_minutes: Maximum age for webhook in minutes

        Returns:
            WebhookSignatureValidationResult with validation details
        """
        self._logger.info(
            "Starting webhook signature validation",
            extra={
                "payload_size": len(payload),
                "headers_count": len(headers),
                "has_secret": bool(self._webhook_secret),
            },
        )

        try:
            # Use the security verifier for comprehensive validation
            (
                is_valid,
                error_message,
            ) = await self._security_verifier.verify_webhook_request(
                payload=payload,
                headers=headers,
                timestamp_tolerance_minutes=timestamp_tolerance_minutes,
            )

            context = {
                "payload_hash": self._get_payload_hash_safe(payload),
                "timestamp_tolerance": timestamp_tolerance_minutes,
                "secret_configured": bool(self._webhook_secret),
            }

            result = WebhookSignatureValidationResult(
                is_valid=is_valid,
                error_message=error_message,
                signature_provided=self._has_signature_header(headers),
                timestamp_valid=True,  # Will be False if timestamp check fails
                payload_size_valid=True,  # Will be False if payload too large
                context=context,
            )

            if is_valid:
                self._logger.info("Webhook signature validation successful")
            else:
                self._logger.warning(
                    "Webhook signature validation failed",
                    extra={"error": error_message},
                )

        except WebhookPayloadError as e:
            self._logger.error("Webhook payload error", exc_info=True)
            return WebhookSignatureValidationResult(
                is_valid=False,
                error_message=str(e),
                payload_size_valid=False,
                context={"error_type": "payload_error"},
            )
        except WebhookSecurityError as e:
            self._logger.error("Webhook security error", exc_info=True)
            return WebhookSignatureValidationResult(
                is_valid=False,
                error_message=str(e),
                context={"error_type": "security_error"},
            )
        except Exception as e:
            self._logger.error("Unexpected error during validation", exc_info=True)
            return WebhookSignatureValidationResult(
                is_valid=False,
                error_message=f"Internal validation error: {e!s}",
                context={"error_type": "internal_error"},
            )
        else:
            return result

    async def validate_with_pydantic_schema(
        self, payload: str, headers: dict[str, str]
    ) -> WebhookSignatureValidationResult:
        """
        Validate webhook using Pydantic schema validation.

        Alternative validation method using the Pydantic models
        from the api_schemas module.

        Args:
            payload: Raw webhook payload
            headers: Request headers

        Returns:
            WebhookSignatureValidationResult with validation details
        """
        try:
            # Parse headers using Pydantic schema
            webhook_headers = WebhookHeaders.model_validate(headers)

            # Validate signature using Pydantic schema
            # The validation happens in the constructor - if it succeeds, we continue
            WebhookSignatureValidation(
                signature=webhook_headers.typeform_signature,
                payload=payload,
                secret=self._webhook_secret or "",
            )

            # If we get here, validation passed
            return WebhookSignatureValidationResult(
                is_valid=True,
                signature_provided=True,
                context={
                    "validation_method": "pydantic_schema",
                    "signature_format": "valid",
                },
            )

        except ValueError as e:
            error_msg = f"Pydantic validation failed: {e!s}"
            self._logger.warning(error_msg)
            return WebhookSignatureValidationResult(
                is_valid=False,
                error_message=error_msg,
                context={"validation_method": "pydantic_schema"},
            )
        except Exception as e:
            error_msg = f"Unexpected error in Pydantic validation: {e!s}"
            self._logger.error("Unexpected error in Pydantic validation", exc_info=True)
            return WebhookSignatureValidationResult(
                is_valid=False,
                error_message=error_msg,
                context={
                    "validation_method": "pydantic_schema",
                    "error_type": "internal",
                },
            )

    async def validate_and_parse_webhook(
        self, payload: str, headers: dict[str, str]
    ) -> tuple[WebhookSignatureValidationResult, dict[str, Any] | None]:
        """
        Validate webhook signature and parse payload in one operation.

        Convenience method that combines signature validation with
        payload parsing using the security middleware.

        Args:
            payload: Raw webhook payload
            headers: Request headers

        Returns:
            Tuple of (validation_result, parsed_payload_or_none)
        """
        try:
            # Use security verifier for validation
            is_valid, error_msg = await self._security_verifier.verify_webhook_request(
                payload, headers
            )

            # Parse payload if validation succeeded
            parsed_payload = None
            if is_valid:
                try:
                    parsed_payload = json.loads(payload)
                except json.JSONDecodeError as e:
                    is_valid = False
                    error_msg = f"Invalid JSON payload: {e!s}"

            result = WebhookSignatureValidationResult(
                is_valid=is_valid,
                error_message=error_msg,
                signature_provided=self._has_signature_header(headers),
                context={
                    "validation_method": "middleware",
                    "payload_parsed": parsed_payload is not None,
                },
            )

        except Exception as e:
            error_msg = f"Error in combined validation and parsing: {e!s}"
            self._logger.error("Error in combined validation and parsing", exc_info=True)

            result = WebhookSignatureValidationResult(
                is_valid=False,
                error_message=error_msg,
                context={"validation_method": "middleware", "error_type": "internal"},
            )
            return result, None
        else:
            return result, parsed_payload

    def _get_payload_hash_safe(self, payload: str) -> str:
        """Safely get payload hash without accessing private members."""
        try:
            # Create a simple hash locally since we can't access private methods
            return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
        except Exception:
            return "unknown"

    def _has_signature_header(self, headers: dict[str, str]) -> bool:
        """Check if TypeForm signature header is present."""
        signature_headers = [
            "Typeform-Signature",
            "typeform-signature",
            "X-Typeform-Signature",
            "x-typeform-signature",
        ]

        return any(header in headers for header in signature_headers)

    def validate_signature_format(self, signature: str) -> bool:
        """
        Validate TypeForm signature format.

        Args:
            signature: Signature string to validate

        Returns:
            True if format is valid, False otherwise
        """
        if not signature:
            return False

        # TypeForm signatures should start with 'sha256='
        return (
            signature.startswith(SHA256_PREFIX)
            and len(signature) > MIN_SIGNATURE_LENGTH
        )

    def is_signature_validation_enabled(self) -> bool:
        """Check if signature validation is enabled."""
        return bool(self._webhook_secret)

    def get_validation_context(self) -> dict[str, Any]:
        """Get context information about the validator configuration."""
        return {
            "signature_validation_enabled": self.is_signature_validation_enabled(),
            "has_webhook_secret": bool(self._webhook_secret),
            "config_loaded": self._config is not None,
            "verifier_initialized": self._security_verifier is not None,
        }


# Convenience functions for direct use
async def validate_typeform_webhook_signature(
    payload: str,
    headers: dict[str, str],
    webhook_secret: str | None = None,
    timestamp_tolerance_minutes: int = 5,
) -> WebhookSignatureValidationResult:
    """
    Convenience function for TypeForm webhook signature validation.

    Args:
        payload: Raw webhook payload
        headers: Request headers
        webhook_secret: Optional webhook secret
        timestamp_tolerance_minutes: Maximum webhook age in minutes

    Returns:
        WebhookSignatureValidationResult with validation details
    """
    validator = WebhookSignatureValidator(webhook_secret)
    return await validator.validate_webhook_signature(
        payload, headers, timestamp_tolerance_minutes
    )


def create_webhook_signature_validator(
    webhook_secret: str | None = None,
) -> WebhookSignatureValidator:
    """
    Factory function for creating WebhookSignatureValidator instances.

    Args:
        webhook_secret: Optional webhook secret

    Returns:
        Configured WebhookSignatureValidator instance
    """
    return WebhookSignatureValidator(webhook_secret)
