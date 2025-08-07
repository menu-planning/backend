"""
Unit tests for webhook security verification.

Tests HMAC-SHA256 signature verification, payload validation,
and timestamp verification for TypeForm webhooks.
"""

import pytest
import base64
import hmac
import hashlib
from unittest.mock import patch
from datetime import datetime, timedelta

from src.contexts.client_onboarding.core.services.webhook_security import (
    WebhookSecurityVerifier,
    verify_typeform_webhook,
)
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookSecurityError,
    WebhookPayloadError,
)

pytestmark = pytest.mark.anyio

@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "test_webhook_secret_123"


@pytest.fixture
def verifier(webhook_secret):
    """Create WebhookSecurityVerifier instance with test secret."""
    return WebhookSecurityVerifier(webhook_secret=webhook_secret)


@pytest.fixture
def sample_payload():
    """Sample TypeForm webhook payload."""
    return '{"event_id":"test_event_123","event_type":"form_response","form_response":{"form_id":"test_form","answers":[]}}'


@pytest.fixture
def sample_headers():
    """Sample HTTP headers."""
    return {
        "Content-Type": "application/json",
        "User-Agent": "Typeform",
        "Typeform-Signature": "sha256=test_signature"
    }


class TestWebhookSecurityVerifier:
    """Test WebhookSecurityVerifier class."""

    def test_init_with_custom_secret(self):
        """Test verifier initialization with custom secret."""
        custom_secret = "custom_secret_456"
        verifier = WebhookSecurityVerifier(webhook_secret=custom_secret)
        assert verifier.webhook_secret == custom_secret

    @patch('src.contexts.client_onboarding.core.services.webhook_security.config')
    def test_init_with_config_secret(self, mock_config):
        """Test verifier initialization using config secret."""
        mock_config.typeform_webhook_secret = "config_secret_789"
        mock_config.webhook_signature_header = "Typeform-Signature"
        mock_config.max_webhook_payload_size = 1048576
        
        verifier = WebhookSecurityVerifier()
        assert verifier.webhook_secret == "config_secret_789"

    def test_init_no_secret_warning(self, caplog):
        """Test warning when no secret is configured."""
        with patch('src.contexts.client_onboarding.core.services.webhook_security.config') as mock_config:
            mock_config.typeform_webhook_secret = None
            mock_config.webhook_signature_header = "Typeform-Signature"
            mock_config.max_webhook_payload_size = 1048576
            
            verifier = WebhookSecurityVerifier(webhook_secret=None)
            assert verifier.webhook_secret is None
            assert "Webhook secret not configured" in caplog.text

    def test_extract_signature_with_sha256_prefix(self, verifier):
        """Test signature extraction with sha256= prefix."""
        # Use realistic 44-character base64 signature (SHA256 hash)
        realistic_signature = "n4bQgYhMfWWaL+qgxVrQFaO/TxsrC4Is0V1sFbDwCgg="
        headers = {"Typeform-Signature": f"sha256={realistic_signature}"}
        signature = verifier._extract_signature(headers)
        assert signature == realistic_signature

    def test_extract_signature_without_prefix(self, verifier):
        """Test signature extraction without sha256= prefix."""
        # Use realistic 44-character base64 signature (SHA256 hash)
        realistic_signature = "n4bQgYhMfWWaL+qgxVrQFaO/TxsrC4Is0V1sFbDwCgg="
        headers = {"Typeform-Signature": realistic_signature}
        signature = verifier._extract_signature(headers)
        # Should return None since prefix is required
        assert signature is None

    def test_extract_signature_case_insensitive(self, verifier):
        """Test signature extraction with case-insensitive header."""
        # Use realistic 44-character base64 signature (SHA256 hash)
        realistic_signature = "n4bQgYhMfWWaL+qgxVrQFaO/TxsrC4Is0V1sFbDwCgg="
        headers = {"typeform-signature": f"sha256={realistic_signature}"}
        signature = verifier._extract_signature(headers)
        assert signature == realistic_signature

    def test_extract_signature_missing_header(self, verifier):
        """Test signature extraction when header is missing."""
        headers = {"Content-Type": "application/json"}
        signature = verifier._extract_signature(headers)
        assert signature is None

    async def test_verify_signature_valid(self, verifier, webhook_secret, sample_payload):
        """Test signature verification with valid signature."""
        # Create valid signature using TypeForm algorithm
        payload_with_newline = sample_payload + '\n'
        computed_hmac = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        result = await verifier._verify_signature(sample_payload, expected_signature)
        assert result is True

    async def test_verify_signature_invalid(self, verifier, sample_payload):
        """Test signature verification with invalid signature."""
        invalid_signature = "invalid_signature_123"
        result = await verifier._verify_signature(sample_payload, invalid_signature)
        assert result is False

    async def test_verify_signature_wrong_secret(self, sample_payload):
        """Test signature verification with wrong secret."""
        wrong_verifier = WebhookSecurityVerifier(webhook_secret="wrong_secret")
        
        # Create signature with correct secret
        correct_secret = "correct_secret"
        payload_with_newline = sample_payload + '\n'
        computed_hmac = hmac.new(
            correct_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        result = await wrong_verifier._verify_signature(sample_payload, expected_signature)
        assert result is False

    async def test_verify_timestamp_valid(self, verifier):
        """Test timestamp verification with valid timestamp."""
        current_timestamp = datetime.now().timestamp()
        headers = {"timestamp": str(current_timestamp)}
        
        result = await verifier._verify_timestamp(headers, tolerance_minutes=5)
        assert result is True

    async def test_verify_timestamp_too_old(self, verifier):
        """Test timestamp verification with old timestamp."""
        old_timestamp = (datetime.now() - timedelta(minutes=10)).timestamp()
        headers = {"timestamp": str(old_timestamp)}
        
        result = await verifier._verify_timestamp(headers, tolerance_minutes=5)
        assert result is False

    async def test_verify_timestamp_future(self, verifier):
        """Test timestamp verification with future timestamp."""
        future_timestamp = (datetime.now() + timedelta(minutes=10)).timestamp()
        headers = {"timestamp": str(future_timestamp)}
        
        result = await verifier._verify_timestamp(headers, tolerance_minutes=5)
        assert result is False

    async def test_verify_timestamp_missing(self, verifier):
        """Test timestamp verification when timestamp is missing."""
        headers = {"Content-Type": "application/json"}
        
        result = await verifier._verify_timestamp(headers, tolerance_minutes=5)
        assert result is True  # Missing timestamp is allowed

    async def test_verify_timestamp_invalid_format(self, verifier):
        """Test timestamp verification with invalid format."""
        headers = {"timestamp": "invalid_timestamp"}
        
        result = await verifier._verify_timestamp(headers, tolerance_minutes=5)
        assert result is False

    async def test_verify_webhook_request_success(self, verifier, webhook_secret, sample_payload):
        """Test complete webhook verification with valid request."""
        # Create valid signature
        payload_with_newline = sample_payload + '\n'
        computed_hmac = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        headers = {
            "Typeform-Signature": f"sha256={signature}",
            "timestamp": str(datetime.now().timestamp())
        }
        
        is_valid, error_msg = await verifier.verify_webhook_request(sample_payload, headers)
        assert is_valid is True
        assert error_msg is None

    async def test_verify_webhook_request_invalid_signature(self, verifier, sample_payload):
        """Test webhook verification with invalid signature."""
        # Use realistic length but invalid signature content (different SHA256 hash)
        invalid_signature = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        headers = {
            "Typeform-Signature": f"sha256={invalid_signature}",
            "timestamp": str(datetime.now().timestamp())
        }
        
        is_valid, error_msg = await verifier.verify_webhook_request(sample_payload, headers)
        assert is_valid is False
        assert error_msg is not None and "Invalid webhook signature" in error_msg

    async def test_verify_webhook_request_missing_signature(self, verifier, sample_payload):
        """Test webhook verification with missing signature."""
        headers = {"timestamp": str(datetime.now().timestamp())}
        
        is_valid, error_msg = await verifier.verify_webhook_request(sample_payload, headers)
        assert is_valid is False
        assert error_msg is not None and "Missing webhook signature" in error_msg

    async def test_verify_webhook_request_no_secret_configured(self, sample_payload, monkeypatch):
        """Test webhook verification when no secret is configured."""
        # Mock config to return empty secret
        monkeypatch.setattr("src.contexts.client_onboarding.core.services.webhook_security.config.typeform_webhook_secret", "")
        
        verifier = WebhookSecurityVerifier(webhook_secret=None)  # Will use empty config value
        headers = {"Content-Type": "application/json"}
        
        is_valid, error_msg = await verifier.verify_webhook_request(sample_payload, headers)
        assert is_valid is True
        assert error_msg is None

    async def test_verify_webhook_request_payload_too_large(self, verifier):
        """Test webhook verification with oversized payload."""
        large_payload = "x" * (verifier.max_payload_size + 1)
        headers = {"Typeform-Signature": "sha256=test"}
        
        with pytest.raises(WebhookPayloadError) as exc_info:
            await verifier.verify_webhook_request(large_payload, headers)
        assert "Payload size exceeds maximum" in str(exc_info.value)

    async def test_verify_webhook_request_timestamp_expired(self, verifier, webhook_secret, sample_payload):
        """Test webhook verification with expired timestamp."""
        # Create valid signature
        payload_with_newline = sample_payload + '\n'
        computed_hmac = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        # Use old timestamp
        old_timestamp = (datetime.now() - timedelta(minutes=10)).timestamp()
        headers = {
            "Typeform-Signature": f"sha256={signature}",
            "timestamp": str(old_timestamp)
        }
        
        is_valid, error_msg = await verifier.verify_webhook_request(
            sample_payload, headers, timestamp_tolerance_minutes=5
        )
        assert is_valid is False
        assert error_msg is not None and "Webhook timestamp outside tolerance" in error_msg

    def test_get_payload_hash(self, verifier, sample_payload):
        """Test payload hash generation."""
        hash_value = verifier._get_payload_hash(sample_payload)
        expected_hash = hashlib.sha256(sample_payload.encode('utf-8')).hexdigest()
        assert hash_value == expected_hash


class TestConvenienceFunction:
    """Test convenience function for webhook verification."""

    async def test_verify_typeform_webhook_success(self, webhook_secret, sample_payload):
        """Test convenience function with valid webhook."""
        # Create valid signature
        payload_with_newline = sample_payload + '\n'
        computed_hmac = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        headers = {
            "Typeform-Signature": f"sha256={signature}",
            "timestamp": str(datetime.now().timestamp())
        }
        
        is_valid, error_msg = await verify_typeform_webhook(
            sample_payload, headers, webhook_secret=webhook_secret
        )
        assert is_valid is True
        assert error_msg is None

    async def test_verify_typeform_webhook_invalid(self, webhook_secret, sample_payload):
        """Test convenience function with invalid webhook."""
        # Use realistic length but invalid signature content (different SHA256 hash)
        invalid_signature = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        headers = {"Typeform-Signature": f"sha256={invalid_signature}"}
        
        is_valid, error_msg = await verify_typeform_webhook(
            sample_payload, headers, webhook_secret=webhook_secret
        )
        assert is_valid is False
        assert error_msg is not None and "Invalid webhook signature" in error_msg


class TestTypeFormAlgorithmCompliance:
    """Test compliance with TypeForm's specific HMAC algorithm."""

    async def test_typeform_algorithm_with_newline(self, webhook_secret):
        """Test that TypeForm algorithm correctly adds newline to payload."""
        payload = '{"test": "data"}'
        
        # TypeForm algorithm: payload + '\n' → HMAC-SHA256 → base64
        payload_with_newline = payload + '\n'
        computed_hmac = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        verifier = WebhookSecurityVerifier(webhook_secret=webhook_secret)
        result = await verifier._verify_signature(payload, expected_signature)
        assert result is True

    async def test_typeform_algorithm_without_newline_fails(self, webhook_secret):
        """Test that algorithm without newline fails (not TypeForm compliant)."""
        payload = '{"test": "data"}'
        
        # Wrong algorithm: payload (no newline) → HMAC-SHA256 → base64
        computed_hmac = hmac.new(
            webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),  # No newline
            hashlib.sha256
        ).digest()
        wrong_signature = base64.b64encode(computed_hmac).decode('utf-8')
        
        verifier = WebhookSecurityVerifier(webhook_secret=webhook_secret)
        result = await verifier._verify_signature(payload, wrong_signature)
        assert result is False

    async def test_secure_comparison_prevents_timing_attacks(self, webhook_secret):
        """Test that hmac.compare_digest is used for secure comparison."""
        payload = '{"test": "data"}'
        verifier = WebhookSecurityVerifier(webhook_secret=webhook_secret)
        
        # Even with wrong signature, function should take consistent time
        # This is more of a code inspection test than timing test
        with patch('hmac.compare_digest') as mock_compare:
            mock_compare.return_value = False
            
            result = await verifier._verify_signature(payload, "wrong_signature")
            
            mock_compare.assert_called_once()
            assert result is False


class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_webhook_security_error_on_unexpected_exception(self, verifier, sample_payload):
        """Test that unexpected exceptions are wrapped in WebhookSecurityError."""
        headers = {"Typeform-Signature": "sha256=test"}
        
        with patch.object(verifier, '_extract_signature', side_effect=Exception("Unexpected error")):
            with pytest.raises(WebhookSecurityError) as exc_info:
                await verifier.verify_webhook_request(sample_payload, headers)
            assert "Unexpected error during webhook verification" in str(exc_info.value)

    async def test_signature_verification_exception_handling(self, verifier):
        """Test signature verification handles exceptions gracefully."""
        with patch('hmac.new', side_effect=Exception("HMAC error")):
            result = await verifier._verify_signature("test_payload", "test_signature")
            assert result is False

    async def test_known_exceptions_are_reraised(self, verifier):
        """Test that known security exceptions are re-raised."""
        large_payload = "x" * (verifier.max_payload_size + 1)
        headers = {"Typeform-Signature": "sha256=test"}
        
        # WebhookPayloadError should be re-raised, not wrapped
        with pytest.raises(WebhookPayloadError):
            await verifier.verify_webhook_request(large_payload, headers) 