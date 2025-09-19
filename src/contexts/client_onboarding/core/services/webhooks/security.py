"""Webhook security verification for TypeForm webhooks.

Provides comprehensive security verification including signature validation,
timestamp verification, replay protection, and payload size validation.
"""

from __future__ import annotations

import base64
import hashlib

# Directly moved from services/webhook_security.py to webhooks/security.py
import hmac
import time
from datetime import UTC, datetime
from typing import ClassVar

import anyio
from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
    WebhookSecurityError,
)
from src.logging.logger import get_logger

logger = get_logger(__name__)


class WebhookSecurityVerifier:
    """Webhook security verifier for TypeForm webhook requests.

    Provides comprehensive security verification including signature validation,
    timestamp verification, replay protection, and payload size validation.
    """

    _replay_window_minutes: int = 10
    _global_replay_cache: ClassVar[dict[str, float]] = {}
    _global_cache_lock: anyio.Lock = anyio.Lock()

    def __init__(self, webhook_secret: str | None = None):
        """Initialize the webhook security verifier.

        Args:
            webhook_secret: Optional webhook secret for signature verification.
        """
        self.webhook_secret = webhook_secret or config.typeform_webhook_secret
        self.signature_header = config.webhook_signature_header
        self.max_payload_size = config.max_webhook_payload_size
        self._processed_requests: set[str] = set()
        if not self.webhook_secret:
            logger.warning(
                "Webhook secret not configured - signature verification disabled",
                security_event="webhook_security_config_warning",
                security_level="high",
                security_risk="signature_verification_disabled",
                business_impact="security_degraded",
                action="webhook_security_init"
            )

    async def verify_webhook_request(
        self,
        payload: str,
        headers: dict[str, str],
        timestamp_tolerance_minutes: int = 5,
    ) -> tuple[bool, str | None]:
        """Verify webhook request security including signature, timestamp, and replay protection.

        Args:
            payload: Raw webhook payload string.
            headers: HTTP headers from the webhook request.
            timestamp_tolerance_minutes: Maximum age for webhook timestamps.

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is None.

        Raises:
            WebhookPayloadError: For payload size violations.
            WebhookSecurityError: For security verification failures.
        """
        try:
            if len(payload.encode("utf-8")) > self.max_payload_size:
                error_msg = f"Payload size exceeds maximum allowed ({self.max_payload_size} bytes)"
                logger.warning(
                    "Webhook payload too large - potential security risk",
                    security_event="webhook_payload_size_violation",
                    security_level="medium",
                    payload_size_bytes=len(payload),
                    max_size_bytes=self.max_payload_size,
                    security_risk="oversized_payload",
                    business_impact="webhook_rejected",
                    action="webhook_security_validation"
                )
                raise WebhookPayloadError(error_msg)
            if not self.webhook_secret:
                logger.warning(
                    "Webhook signature verification skipped - no secret configured",
                    security_event="webhook_signature_skipped",
                    security_level="high",
                    security_risk="no_signature_verification",
                    business_impact="security_degraded",
                    action="webhook_security_bypass"
                )
                return True, None
            signature = self._extract_signature(headers)
            if not signature:
                error_msg = "Missing webhook signature in headers"
                logger.warning(
                    "Missing webhook signature header - potential security risk",
                    security_event="webhook_signature_missing",
                    security_level="high",
                    expected_header=self.signature_header,
                    security_risk="missing_signature",
                    business_impact="webhook_rejected",
                    action="webhook_security_validation"
                )
                return False, error_msg
            is_valid = await self._verify_signature(payload, signature)
            if not is_valid:
                error_msg = "Invalid webhook signature"
                logger.warning(
                    "Signature verification failed - potential security threat",
                    security_event="webhook_signature_invalid",
                    security_level="high",
                    payload_hash_prefix=self._get_payload_hash(payload)[:8],
                    security_risk="invalid_signature",
                    business_impact="webhook_rejected",
                    action="webhook_security_validation"
                )
                return False, error_msg
            timestamp_valid = await self._verify_timestamp(
                headers, timestamp_tolerance_minutes
            )
            if not timestamp_valid:
                error_msg = f"Webhook timestamp outside tolerance ({timestamp_tolerance_minutes} minutes)"
                logger.warning(
                    "Webhook timestamp verification failed - potential replay attack",
                    security_event="webhook_timestamp_invalid",
                    security_level="medium",
                    security_risk="timestamp_outside_tolerance",
                    business_impact="webhook_rejected",
                    action="webhook_security_validation"
                )
                return False, error_msg
            is_replay = await self._check_replay_protection(payload, headers)
            if is_replay:
                error_msg = "Potential replay attack detected"
                logger.warning(
                    "Replay attack detected - security threat blocked",
                    security_event="webhook_replay_attack",
                    security_level="critical",
                    payload_hash_prefix=self._get_payload_hash(payload)[:8],
                    security_risk="replay_attack",
                    business_impact="webhook_rejected",
                    action="webhook_security_validation"
                )
                return False, error_msg
            logger.info(
                "Webhook signature verification successful",
                security_event="webhook_signature_verified",
                security_level="info",
                security_validation="signature_valid",
                business_context="webhook_security",
                action="webhook_security_success"
            )
            return True, None
        except (WebhookSecurityError, WebhookPayloadError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error during webhook verification: {e!s}"
            logger.error(error_msg, exc_info=True)
            raise WebhookSecurityError(error_msg) from e

    def _extract_signature(self, headers: dict[str, str]) -> str | None:
        """Extract and validate webhook signature from headers.

        Args:
            headers: HTTP headers from the webhook request.

        Returns:
            Extracted signature hash or None if not found/invalid.
        """
        signature_value = headers.get(self.signature_header)
        if not signature_value:
            signature_value = headers.get(self.signature_header.lower())
        if not signature_value:
            return None
        if not signature_value.startswith("sha256="):
            logger.warning(
                f"Invalid signature format: missing or incorrect prefix: {signature_value[:20]}..."
            )
            return None
        if signature_value != signature_value.strip():
            logger.warning("Invalid signature format: contains whitespace")
            return None
        signature_hash = signature_value[7:]
        if len(signature_hash) not in [44, 64]:
            logger.warning(
                f"Invalid signature format: incorrect length {len(signature_hash)}, expected 44 (base64) or 64 (hex)"
            )
            return None
        try:
            if len(signature_hash) == 44:
                base64.b64decode(signature_hash)
            elif len(signature_hash) == 64:
                bytes.fromhex(signature_hash)
        except Exception:
            logger.warning("Invalid signature format: not valid base64 or hex")
            return None
        return signature_hash

    async def _verify_signature(self, payload: str, expected_signature: str) -> bool:
        """Verify webhook signature using HMAC-SHA256.

        Args:
            payload: Raw webhook payload string.
            expected_signature: Expected signature hash from headers.

        Returns:
            True if signature is valid, False otherwise.
        """
        try:
            payload_with_newline = payload + "\n"
            secret_bytes = self.webhook_secret.encode("utf-8")
            payload_bytes = payload_with_newline.encode("utf-8")
            computed_hmac = hmac.new(
                secret_bytes, payload_bytes, hashlib.sha256
            ).digest()
            computed_signature = base64.b64encode(computed_hmac).decode("utf-8")
            return hmac.compare_digest(computed_signature, expected_signature)
        except Exception as e:
            logger.error("Error computing webhook signature", error=str(e), exc_info=True)
            return False

    async def _verify_timestamp(
        self, headers: dict[str, str], tolerance_minutes: int
    ) -> bool:
        """Verify webhook timestamp is within acceptable tolerance.

        Args:
            headers: HTTP headers from the webhook request.
            tolerance_minutes: Maximum age for webhook timestamps in minutes.

        Returns:
            True if timestamp is valid or not present, False if too old.
        """
        timestamp_header = (
            headers.get("x-typeform-timestamp")
            or headers.get("timestamp")
            or headers.get("x-timestamp")
        )
        if not timestamp_header:
            return True
        try:
            webhook_timestamp = datetime.fromtimestamp(
                float(timestamp_header), tz=UTC
            )
            current_time = datetime.now(UTC)
            time_diff = abs((current_time - webhook_timestamp).total_seconds())
            max_diff_seconds = tolerance_minutes * 60
            if time_diff > max_diff_seconds:
                logger.warning("Webhook timestamp too old", time_diff_seconds=time_diff, max_diff_seconds=max_diff_seconds)
                return False
            return True
        except (ValueError, TypeError) as e:
            logger.warning("Invalid timestamp format", timestamp_header=timestamp_header, error=str(e))
            return False

    async def _check_replay_protection(
        self, payload: str, headers: dict[str, str]
    ) -> bool:
        """Check for potential replay attacks using request fingerprinting.

        Args:
            payload: Raw webhook payload string.
            headers: HTTP headers from the webhook request.

        Returns:
            True if replay attack detected, False otherwise.
        """
        payload_hash = self._get_payload_hash(payload)
        signature = self._extract_signature(headers)
        request_fingerprint = f"{payload_hash}:{signature}"
        now = time.time()
        ttl_seconds = self._replay_window_minutes * 60
        async with self._global_cache_lock:
            if self._global_replay_cache:
                expired_keys = [
                    k for k, exp in self._global_replay_cache.items() if exp <= now
                ]
                for k in expired_keys:
                    self._global_replay_cache.pop(k, None)
            if request_fingerprint in self._global_replay_cache:
                return True
            self._global_replay_cache[request_fingerprint] = now + ttl_seconds
            if len(self._global_replay_cache) > 5000:
                sorted_items = sorted(
                    self._global_replay_cache.items(), key=lambda item: item[1]
                )
                halfway_index = len(sorted_items) // 2
                for k, _ in sorted_items[:halfway_index]:
                    self._global_replay_cache.pop(k, None)
                logger.debug("Cleaned up replay protection cache (size-based)")
        return False

    @classmethod
    async def mark_request_processed(
        cls, payload: str, headers: dict[str, str]
    ) -> None:
        """Mark a webhook request as processed for replay protection.

        Args:
            payload: Raw webhook payload string.
            headers: HTTP headers from the webhook request.
        """
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        signature_value = headers.get(config.webhook_signature_header) or headers.get(
            config.webhook_signature_header.lower()
        )
        if not signature_value:
            return
        if signature_value.startswith("sha256="):
            signature_value = signature_value[7:]
        request_fingerprint = f"{payload_hash}:{signature_value}"
        now = time.time()
        ttl_seconds = cls._replay_window_minutes * 60
        async with cls._global_cache_lock:
            if cls._global_replay_cache:
                expired_keys = [
                    k for k, exp in cls._global_replay_cache.items() if exp <= now
                ]
                for k in expired_keys:
                    cls._global_replay_cache.pop(k, None)
            cls._global_replay_cache[request_fingerprint] = now + ttl_seconds



    def _get_payload_hash(self, payload: str) -> str:
        """Generate SHA256 hash of the payload for fingerprinting.

        Args:
            payload: Raw webhook payload string.

        Returns:
            SHA256 hash of the payload as hexadecimal string.
        """
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def verify_typeform_webhook(
    payload: str,
    headers: dict[str, str],
    webhook_secret: str | None = None,
    timestamp_tolerance_minutes: int = 5,
) -> tuple[bool, str | None]:
    """Convenience function to verify TypeForm webhook security.

    Args:
        payload: Raw webhook payload string.
        headers: HTTP headers from the webhook request.
        webhook_secret: Optional webhook secret for signature verification.
        timestamp_tolerance_minutes: Maximum age for webhook timestamps.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.

    Raises:
        WebhookPayloadError: For payload size violations.
        WebhookSecurityError: For security verification failures.
    """
    verifier = WebhookSecurityVerifier(webhook_secret)
    return await verifier.verify_webhook_request(
        payload, headers, timestamp_tolerance_minutes
    )
