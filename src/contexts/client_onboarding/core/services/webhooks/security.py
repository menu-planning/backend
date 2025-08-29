from __future__ import annotations

# Directly moved from services/webhook_security.py to webhooks/security.py

import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, Tuple, Set
from datetime import datetime, timezone
import anyio
import asyncio
import time

from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookSecurityError,
    WebhookPayloadError,
)

logger = logging.getLogger(__name__)


class WebhookSecurityVerifier:
    _replay_window_minutes: int = 10
    _global_replay_cache: dict[str, float] = {}
    _global_cache_lock: asyncio.Lock = asyncio.Lock()

    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret or config.typeform_webhook_secret
        self.signature_header = config.webhook_signature_header
        self.max_payload_size = config.max_webhook_payload_size
        self._processed_requests: Set[str] = set()
        self._cleanup_task = None
        if not self.webhook_secret:
            logger.warning(
                "Webhook secret not configured - signature verification disabled"
            )

    async def verify_webhook_request(
        self,
        payload: str,
        headers: Dict[str, str],
        timestamp_tolerance_minutes: int = 5,
    ) -> Tuple[bool, Optional[str]]:
        try:
            if len(payload.encode("utf-8")) > self.max_payload_size:
                error_msg = f"Payload size exceeds maximum allowed ({self.max_payload_size} bytes)"
                logger.warning(f"Webhook payload too large: {len(payload)} bytes")
                raise WebhookPayloadError(error_msg)
            if not self.webhook_secret:
                logger.warning(
                    "Webhook signature verification skipped - no secret configured"
                )
                return True, None
            signature = self._extract_signature(headers)
            if not signature:
                error_msg = "Missing webhook signature in headers"
                logger.warning(f"Missing signature header: {self.signature_header}")
                return False, error_msg
            is_valid = await self._verify_signature(payload, signature)
            if not is_valid:
                error_msg = "Invalid webhook signature"
                logger.warning(
                    f"Signature verification failed for payload hash: {self._get_payload_hash(payload)[:8]}..."
                )
                return False, error_msg
            timestamp_valid = await self._verify_timestamp(
                headers, timestamp_tolerance_minutes
            )
            if not timestamp_valid:
                error_msg = f"Webhook timestamp outside tolerance ({timestamp_tolerance_minutes} minutes)"
                logger.warning("Webhook timestamp verification failed")
                return False, error_msg
            is_replay = await self._check_replay_protection(payload, headers)
            if is_replay:
                error_msg = "Potential replay attack detected"
                logger.warning(
                    f"Replay attack detected for payload hash: {self._get_payload_hash(payload)[:8]}..."
                )
                return False, error_msg
            logger.info("Webhook signature verification successful")
            return True, None
        except (WebhookSecurityError, WebhookPayloadError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error during webhook verification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise WebhookSecurityError(error_msg)

    def _extract_signature(self, headers: Dict[str, str]) -> Optional[str]:
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
            logger.error(f"Error computing webhook signature: {e}")
            return False

    async def _verify_timestamp(
        self, headers: Dict[str, str], tolerance_minutes: int
    ) -> bool:
        timestamp_header = (
            headers.get("x-typeform-timestamp")
            or headers.get("timestamp")
            or headers.get("x-timestamp")
        )
        if not timestamp_header:
            return True
        try:
            webhook_timestamp = datetime.fromtimestamp(
                float(timestamp_header), tz=timezone.utc
            )
            current_time = datetime.now(timezone.utc)
            time_diff = abs((current_time - webhook_timestamp).total_seconds())
            max_diff_seconds = tolerance_minutes * 60
            if time_diff > max_diff_seconds:
                logger.warning(f"Webhook timestamp too old: {time_diff} seconds")
                return False
            return True
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid timestamp format: {timestamp_header}, error: {e}")
            return False

    async def _check_replay_protection(
        self, payload: str, headers: Dict[str, str]
    ) -> bool:
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
        cls, payload: str, headers: Dict[str, str]
    ) -> None:
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

    async def _cleanup_old_requests(self) -> None:
        try:
            await anyio.sleep(self._replay_window_minutes * 60)
            self._processed_requests.clear()
            logger.debug("Cleaned up replay protection cache")
        except anyio.get_cancelled_exc_class():
            pass
        except Exception as e:
            logger.error(f"Error in replay protection cleanup: {e}")

    def _get_payload_hash(self, payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def verify_typeform_webhook(
    payload: str,
    headers: Dict[str, str],
    webhook_secret: Optional[str] = None,
    timestamp_tolerance_minutes: int = 5,
) -> Tuple[bool, Optional[str]]:
    verifier = WebhookSecurityVerifier(webhook_secret)
    return await verifier.verify_webhook_request(
        payload, headers, timestamp_tolerance_minutes
    )
