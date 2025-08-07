"""
Webhook Security Utilities for Testing

Provides utilities for testing webhook signature validation with both
valid and invalid scenarios. Supports TypeForm webhook signature format.

This module provides:
- Signature generation for valid webhook scenarios
- Invalid signature generation for error testing
- Signature validation testing utilities
- Security scenario factories
"""

import hashlib
import hmac
import logging
from typing import Dict, Any, Optional
import json
import base64

from tests.utils.counter_manager import get_next_webhook_counter

logger = logging.getLogger(__name__)


class WebhookSecurityHelper:
    """
    Helper class for testing webhook signature validation.
    
    Provides methods to generate valid and invalid signatures for testing
    various security scenarios.
    """
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize webhook security helper.
        
        Args:
            secret: Webhook secret for signature generation
        """
        self.secret = secret or self._generate_test_secret()
    
    def _generate_test_secret(self) -> str:
        """Generate a deterministic test secret."""
        counter = get_next_webhook_counter()
        return f"test_webhook_secret_{counter:03d}"
    
    def generate_valid_signature(self, payload) -> str:
        """
        Generate a valid TypeForm webhook signature.
        
        Args:
            payload: Webhook payload to sign (can be dict or string)
            
        Returns:
            Valid signature string
        """
        # Handle both dict and string inputs
        if isinstance(payload, dict):
            # Convert payload to JSON string (ensure consistent Unicode handling)
            payload_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        else:
            # Assume it's already a JSON string
            payload_json = payload
        
        # TypeForm specific: Add newline to payload before hashing
        payload_with_newline = payload_json + '\n'
        payload_bytes = payload_with_newline.encode('utf-8')
        
        # Generate HMAC-SHA256 signature
        computed_hmac = hmac.new(
            self.secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).digest()
        
        # Base64 encode the result (TypeForm's format)
        signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        return f"sha256={signature}"
    
    def generate_invalid_signature(self, signature_type: str = "invalid_secret") -> str:
        """
        Generate an invalid signature for testing error scenarios.
        
        Args:
            signature_type: Type of invalid signature to generate
                - "invalid_secret": Wrong secret used
                - "malformed": Malformed signature format
                - "wrong_algorithm": Wrong algorithm used
                - "empty": Empty signature
                
        Returns:
            Invalid signature string
        """
        counter = get_next_webhook_counter()
        
        if signature_type == "invalid_secret":
            # Use wrong secret
            wrong_secret = f"wrong_secret_{counter}"
            
            # Use a test payload with correct algorithm but wrong secret
            test_payload = '{"test": "payload"}\n'
            computed_hmac = hmac.new(
                wrong_secret.encode('utf-8'),
                test_payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature = base64.b64encode(computed_hmac).decode('utf-8')
            return f"sha256={signature}"
        
        elif signature_type == "malformed":
            return f"invalid_format_{counter}"
        
        elif signature_type == "wrong_algorithm":
            # Use correct secret but wrong algorithm (md5 instead of sha256)
            test_payload = '{"test": "payload"}\n'
            computed_hmac = hmac.new(
                self.secret.encode('utf-8'),
                test_payload.encode('utf-8'),
                hashlib.md5  # Wrong algorithm
            ).digest()
            signature = base64.b64encode(computed_hmac).decode('utf-8')
            return f"md5={signature}"
        
        elif signature_type == "empty":
            return ""
        
        else:
            return f"unknown_type_{counter}"
    
    def create_valid_headers(self, payload: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """
        Create valid webhook headers with proper signature.
        
        Args:
            payload: Webhook payload to sign
            **kwargs: Additional header overrides
            
        Returns:
            Dict with valid headers including signature
        """
        signature = self.generate_valid_signature(payload)
        
        headers = {
            "Typeform-Signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "Typeform-Webhooks/1.0",
            "Content-Length": str(len(json.dumps(payload))),
            **kwargs
        }
        
        return headers
    
    def create_valid_headers_for_json_payload(self, payload_str: str, **kwargs) -> Dict[str, str]:
        """
        Create valid webhook headers with proper signature for JSON string payload.
        
        This method ensures consistent signature generation when payload is already
        serialized to JSON string.
        
        Args:
            payload_str: JSON-serialized webhook payload
            **kwargs: Additional header overrides
            
        Returns:
            Dict with valid headers including signature
        """
        signature = self.generate_valid_signature(payload_str)
        
        headers = {
            "Typeform-Signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "Typeform-Webhooks/1.0",
            "Content-Length": str(len(payload_str)),
            **kwargs
        }
        
        return headers
    
    def create_invalid_headers(self, payload: Dict[str, Any], 
                             signature_type: str = "invalid_secret",
                             **kwargs) -> Dict[str, str]:
        """
        Create invalid webhook headers for testing error scenarios.
        
        Args:
            payload: Webhook payload
            signature_type: Type of invalid signature to generate
            **kwargs: Additional header overrides
            
        Returns:
            Dict with invalid headers
        """
        invalid_signature = self.generate_invalid_signature(signature_type)
        
        headers = {
            "Typeform-Signature": invalid_signature,
            "Content-Type": "application/json",
            "User-Agent": "Typeform-Webhooks/1.0",
            "Content-Length": str(len(json.dumps(payload))),
            **kwargs
        }
        
        return headers
    
    def create_missing_signature_headers(self, payload: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """
        Create headers without signature for testing missing signature scenarios.
        
        Args:
            payload: Webhook payload
            **kwargs: Additional header overrides
            
        Returns:
            Dict with headers missing signature
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Typeform-Webhooks/1.0",
            "Content-Length": str(len(json.dumps(payload))),
            **kwargs
        }
        
        return headers
    
    def validate_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Validate a webhook signature (for testing validation logic).
        
        Args:
            payload: Webhook payload
            signature: Signature to validate
            
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = self.generate_valid_signature(payload)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False


# =============================================================================
# SECURITY SCENARIO FACTORIES
# =============================================================================

def create_valid_webhook_security_scenario(**kwargs) -> Dict[str, Any]:
    """
    Create a valid webhook security scenario for testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with valid security scenario data
    """
    from tests.contexts.client_onboarding.data_factories.typeform_factories import (
        create_webhook_payload_kwargs
    )
    
    # Create test payload with proper handling of nested overrides
    payload_overrides = kwargs.get("payload", {})
    
    # If form_response overrides are provided, handle them specially
    if "form_response" in payload_overrides:
        form_response_overrides = payload_overrides["form_response"]
        # Remove form_response from payload_overrides to avoid conflicts
        payload_kwargs = {k: v for k, v in payload_overrides.items() if k != "form_response"}
        # Pass form_response overrides as separate kwargs
        payload_kwargs["form_response"] = form_response_overrides
        payload = create_webhook_payload_kwargs(**payload_kwargs)
    else:
        payload = create_webhook_payload_kwargs(**payload_overrides)
    
    # Create security helper
    secret = kwargs.get("secret", "test_secret_123")
    security_helper = WebhookSecurityHelper(secret)
    
    # Serialize payload consistently
    payload_str = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    
    # Generate valid signature and headers for the serialized payload
    headers = security_helper.create_valid_headers_for_json_payload(payload_str)
    
    # Build scenario, excluding payload from kwargs since we've already processed it
    scenario = {
        "payload": payload,
        "payload_str": payload_str,  # Include serialized version for consistent use
        "headers": headers,
        "secret": secret,
        "security_helper": security_helper,
        "is_valid": True,
        **{k: v for k, v in kwargs.items() if k != "payload"}
    }
    
    return scenario


def create_invalid_webhook_security_scenario(signature_type: str = "invalid_secret", 
                                           **kwargs) -> Dict[str, Any]:
    """
    Create an invalid webhook security scenario for testing.
    
    Args:
        signature_type: Type of invalid signature to generate
        **kwargs: Override any default values
        
    Returns:
        Dict with invalid security scenario data
    """
    from tests.contexts.client_onboarding.data_factories.typeform_factories import (
        create_webhook_payload_kwargs
    )
    
    # Create test payload
    payload = create_webhook_payload_kwargs(**kwargs.get("payload", {}))
    
    # Create security helper
    secret = kwargs.get("secret", "test_secret_123")
    security_helper = WebhookSecurityHelper(secret)
    
    # Generate invalid signature and headers
    if signature_type == "missing":
        headers = security_helper.create_missing_signature_headers(payload)
    else:
        headers = security_helper.create_invalid_headers(payload, signature_type)
    
    scenario = {
        "payload": payload,
        "headers": headers,
        "secret": secret,
        "security_helper": security_helper,
        "is_valid": False,
        "signature_type": signature_type,
        **kwargs
    }
    
    return scenario


def create_multiple_security_scenarios(**kwargs) -> Dict[str, Dict[str, Any]]:
    """
    Create multiple security scenarios for comprehensive testing.
    
    Args:
        **kwargs: Common overrides for all scenarios
        
    Returns:
        Dict with various security scenarios
    """
    scenarios = {
        "valid": create_valid_webhook_security_scenario(**kwargs),
        "invalid_secret": create_invalid_webhook_security_scenario("invalid_secret", **kwargs),
        "malformed_signature": create_invalid_webhook_security_scenario("malformed", **kwargs),
        "wrong_algorithm": create_invalid_webhook_security_scenario("wrong_algorithm", **kwargs),
        "empty_signature": create_invalid_webhook_security_scenario("empty", **kwargs),
        "missing_signature": create_invalid_webhook_security_scenario("missing", **kwargs),
    }
    
    return scenarios


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_webhook_security_helper(**kwargs) -> WebhookSecurityHelper:
    """
    Create a WebhookSecurityHelper instance with sensible defaults.
    
    Args:
        **kwargs: Arguments to pass to WebhookSecurityHelper constructor
        
    Returns:
        Configured security helper instance
    """
    return WebhookSecurityHelper(**kwargs)


def simulate_signature_validation_attack(**kwargs) -> Dict[str, Any]:
    """
    Simulate various signature validation attacks for security testing.
    
    Args:
        **kwargs: Attack scenario parameters
        
    Returns:
        Dict with attack scenario data
    """
    counter = get_next_webhook_counter()
    
    attack_scenarios = {
        "timing_attack": {
            "type": "timing_attack",
            "description": "Attempt to exploit timing differences in signature validation",
            "signatures": [
                f"sha256={'a' * 64}",
                f"sha256={'b' * 64}",
                f"sha256={'c' * 64}",
            ]
        },
        "length_extension": {
            "type": "length_extension",
            "description": "Attempt hash length extension attack",
            "signatures": [
                f"sha256=valid_signature_with_extra_data_{counter}",
            ]
        },
        "replay_attack": {
            "type": "replay_attack",
            "description": "Attempt to replay previously valid signatures",
            "signatures": [
                "sha256=previously_valid_signature_123",
            ]
        }
    }
    
    selected_attack = kwargs.get("attack_type", "timing_attack")
    return attack_scenarios.get(selected_attack, attack_scenarios["timing_attack"])


def validate_security_test_coverage(test_scenarios: Dict[str, Any]) -> Dict[str, bool]:
    """
    Validate that security test scenarios provide adequate coverage.
    
    Args:
        test_scenarios: Dict of test scenarios to validate
        
    Returns:
        Dict with coverage validation results
    """
    required_scenarios = [
        "valid",
        "invalid_secret", 
        "malformed_signature",
        "missing_signature",
        "wrong_algorithm",
        "empty_signature"
    ]
    
    coverage = {}
    for scenario in required_scenarios:
        coverage[scenario] = scenario in test_scenarios
    
    coverage["complete"] = all(coverage.values())
    
    return coverage 