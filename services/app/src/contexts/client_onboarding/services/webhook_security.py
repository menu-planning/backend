"""
Webhook security verification for TypeForm webhooks.

This module provides secure signature verification for incoming TypeForm webhooks
to ensure authenticity and prevent unauthorized access.
"""

import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timezone

from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.services.exceptions import (
    WebhookSecurityError,
    WebhookPayloadError,
)

logger = logging.getLogger(__name__)


class WebhookSecurityVerifier:
    """
    Security verification service for TypeForm webhooks.
    
    Handles signature verification, payload size validation,
    and other security checks for incoming webhook requests.
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook security verifier.
        
        Args:
            webhook_secret: Optional webhook secret. If not provided, uses config.
        """
        self.webhook_secret = webhook_secret or config.typeform_webhook_secret
        self.signature_header = config.webhook_signature_header
        self.max_payload_size = config.max_webhook_payload_size
        
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured - signature verification disabled")
    
    async def verify_webhook_request(
        self,
        payload: str,
        headers: Dict[str, str],
        timestamp_tolerance_minutes: int = 5
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify the authenticity of a TypeForm webhook request.
        
        Args:
            payload: Raw webhook payload as string
            headers: HTTP headers from the request
            timestamp_tolerance_minutes: Maximum age for webhook in minutes
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
            
        Raises:
            WebhookSecurityError: For critical security violations
            WebhookPayloadError: For malformed payloads
        """
        try:
            # Check payload size limits
            if len(payload.encode('utf-8')) > self.max_payload_size:
                error_msg = f"Payload size exceeds maximum allowed ({self.max_payload_size} bytes)"
                logger.warning(f"Webhook payload too large: {len(payload)} bytes")
                raise WebhookPayloadError(error_msg)
            
            # Skip signature verification if no secret configured
            if not self.webhook_secret:
                logger.warning("Webhook signature verification skipped - no secret configured")
                return True, None
            
            # Extract signature from headers
            signature = self._extract_signature(headers)
            if not signature:
                error_msg = "Missing webhook signature in headers"
                logger.warning(f"Missing signature header: {self.signature_header}")
                return False, error_msg
            
            # Verify signature
            is_valid = await self._verify_signature(payload, signature)
            if not is_valid:
                error_msg = "Invalid webhook signature"
                logger.warning(f"Signature verification failed for payload hash: {self._get_payload_hash(payload)[:8]}...")
                return False, error_msg
            
            # Optional: Verify timestamp if available
            timestamp_valid = await self._verify_timestamp(
                headers, 
                timestamp_tolerance_minutes
            )
            if not timestamp_valid:
                error_msg = f"Webhook timestamp outside tolerance ({timestamp_tolerance_minutes} minutes)"
                logger.warning("Webhook timestamp verification failed")
                return False, error_msg
            
            logger.info("Webhook signature verification successful")
            return True, None
            
        except (WebhookSecurityError, WebhookPayloadError):
            # Re-raise known security exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error during webhook verification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise WebhookSecurityError(error_msg)

    
    def _extract_signature(self, headers: Dict[str, str]) -> Optional[str]:
        """
        Extract TypeForm signature from request headers.
        
        Args:
            headers: HTTP headers dictionary
            
        Returns:
            Signature string or None if not found
        """
        # TypeForm signatures are typically in format: "sha256=<signature>"
        signature_value = headers.get(self.signature_header)
        if not signature_value:
            # Try common case variations
            signature_value = headers.get(self.signature_header.lower())
        
        if signature_value and signature_value.startswith('sha256='):
            return signature_value[7:]  # Remove 'sha256=' prefix
        
        return signature_value
    
    async def _verify_signature(self, payload: str, expected_signature: str) -> bool:
        """
        Verify HMAC signature for webhook payload using TypeForm's algorithm.
        
        TypeForm algorithm: payload + '\n' → HMAC-SHA256 → base64 encode → 'sha256=' prefix
        
        Args:
            payload: Raw webhook payload
            expected_signature: Expected signature from headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # TypeForm specific: Add newline to payload before hashing
            payload_with_newline = payload + '\n'
            
            # Create HMAC signature using webhook secret
            secret_bytes = self.webhook_secret.encode('utf-8')
            payload_bytes = payload_with_newline.encode('utf-8')
            
            # Compute HMAC-SHA256
            computed_hmac = hmac.new(
                secret_bytes,
                payload_bytes,
                hashlib.sha256
            ).digest()
            
            # Base64 encode the result (TypeForm's format)
            computed_signature = base64.b64encode(computed_hmac).decode('utf-8')
            
            # Use secure comparison to prevent timing attacks
            return hmac.compare_digest(computed_signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error computing webhook signature: {e}")
            return False
    
    async def _verify_timestamp(
        self, 
        headers: Dict[str, str], 
        tolerance_minutes: int
    ) -> bool:
        """
        Verify webhook timestamp to prevent replay attacks.
        
        Args:
            headers: HTTP headers containing timestamp
            tolerance_minutes: Maximum allowed age in minutes
            
        Returns:
            True if timestamp is within tolerance, False otherwise
        """
        # Check for various timestamp header formats (TypeForm uses x-typeform-timestamp)
        timestamp_header = (headers.get('x-typeform-timestamp') or 
                           headers.get('timestamp') or 
                           headers.get('x-timestamp'))
        if not timestamp_header:
            # If no timestamp provided, allow request (optional feature)
            return True
            
        try:
            # Parse timestamp (assume Unix timestamp)
            webhook_timestamp = datetime.fromtimestamp(float(timestamp_header), tz=timezone.utc)
            current_time = datetime.now(timezone.utc)
            
            # Check if within tolerance
            time_diff = abs((current_time - webhook_timestamp).total_seconds())
            max_diff_seconds = tolerance_minutes * 60
            
            if time_diff > max_diff_seconds:
                logger.warning(f"Webhook timestamp too old: {time_diff} seconds")
                return False
                
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid timestamp format: {timestamp_header}, error: {e}")
            return False
    
    def _get_payload_hash(self, payload: str) -> str:
        """Get SHA256 hash of payload for logging purposes."""
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()


async def verify_typeform_webhook(
    payload: str,
    headers: Dict[str, str],
    webhook_secret: Optional[str] = None,
    timestamp_tolerance_minutes: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function for verifying TypeForm webhook requests.
    
    Args:
        payload: Raw webhook payload as string
        headers: HTTP headers from the request
        webhook_secret: Optional webhook secret (uses config if not provided)
        timestamp_tolerance_minutes: Maximum age for webhook in minutes
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
        
    Raises:
        WebhookSecurityError: For critical security violations
        WebhookPayloadError: For malformed payloads
    """
    verifier = WebhookSecurityVerifier(webhook_secret)
    return await verifier.verify_webhook_request(
        payload, 
        headers, 
        timestamp_tolerance_minutes
    ) 