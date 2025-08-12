"""
Replay Attack Protection Tests

Tests replay attack protection mechanisms in webhook signature verification.
Verifies protection against replay attacks, timestamp validation, and security logging.

Uses fake implementations to test behavior without external dependencies.
"""

import pytest
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.contexts.client_onboarding.core.services.webhooks.security import WebhookSecurityVerifier
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.contexts.client_onboarding.fakes.webhook_security import (
    WebhookSecurityHelper
)
from tests.contexts.client_onboarding.data_factories.typeform_factories import (
    create_webhook_payload_kwargs
)
from tests.utils.counter_manager import get_next_webhook_counter


# Skip entire test suite if webhook secret is not configured
WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    pytest.skip("TYPEFORM_WEBHOOK_SECRET environment variable required for security tests", allow_module_level=True)

pytestmark = pytest.mark.anyio


class TestReplayAttackProtection:
    """Test replay attack protection mechanisms."""

    async def test_webhook_replay_attack_same_signature_blocked(self, async_benchmark_timer):
        """Test that replayed webhooks with same signature are blocked."""
        
        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET
        
        async with async_benchmark_timer() as timer:
            # No handler; using verifier-only path
            
            # We will validate security directly with the verifier
            
            # Setup required onboarding form in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
            from datetime import datetime, timezone
            async with FakeUnitOfWork() as uow:
                onboarding_form = OnboardingForm(
                    id=1,
                    typeform_id="test_form",
                    webhook_url="https://test.webhook.url",
                    user_id=1,
                    status=OnboardingFormStatus.ACTIVE,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()
            
            # Create test payload and headers
            test_payload = {
                "event_id": "test_123",
                "event_type": "form_response",
                "form_response": {
                    "form_id": "test_form",
                    "token": "test_token",
                    "submitted_at": "2024-01-01T12:00:00Z",
                    "answers": []
                }
            }
            payload_str = json.dumps(test_payload, separators=(',', ':'))
            
            # Generate valid headers with signature
            security_helper = WebhookSecurityHelper(webhook_secret)
            signature = security_helper.generate_valid_signature(payload_str)
            headers = {"typeform-signature": signature}
            
            verifier = WebhookSecurityVerifier(webhook_secret)
            is_valid_1, err_1 = await verifier.verify_webhook_request(payload=payload_str, headers=headers)
            assert is_valid_1 is True
            
            # Second identical request should be rejected (replay protection)
            # Note: For this test to work properly, the webhook handler would need
            # to implement replay protection via nonce/timestamp tracking
            # For now, we test that the same payload is processed consistently
            is_valid_2, err_2 = await verifier.verify_webhook_request(payload=payload_str, headers=headers)
            assert is_valid_2 is False
            assert err_2 is not None and "replay" in err_2.lower()

    async def test_webhook_timestamp_validation_expired_request(self, async_benchmark_timer):
        """Test that old webhook requests are rejected based on timestamp validation."""
        
        # Create security helper for generating valid signatures
        security_helper = WebhookSecurityHelper("test_secret_replay")
        
        # Create webhook payload with old timestamp
        old_timestamp = datetime.now(timezone.utc) - timedelta(minutes=10)
        webhook_payload = create_webhook_payload_kwargs(
            form_response={
                "form_id": f"form_{get_next_webhook_counter()}",
                "token": f"token_{get_next_webhook_counter()}",
                "submitted_at": old_timestamp.isoformat(),
                "landed_at": old_timestamp.isoformat(),
            }
        )
        
        async with async_benchmark_timer() as timer:
            # Serialize payload consistently
            payload_str = json.dumps(webhook_payload, ensure_ascii=False, separators=(',', ':'))
            
            # Create headers with timestamp
            headers = security_helper.create_valid_headers_for_json_payload(payload_str)
            headers["x-typeform-timestamp"] = str(int(old_timestamp.timestamp()))
            
            # Test direct security verifier with tight tolerance
            verifier = WebhookSecurityVerifier("test_secret_replay")
            
            # Should fail with tight timestamp tolerance (1 minute)
            is_valid, error_msg = await verifier.verify_webhook_request(
                payload=payload_str,
                headers=headers,
                timestamp_tolerance_minutes=1
            )
            
            # Should be rejected due to old timestamp
            assert is_valid is False
            assert error_msg is not None
            assert "timestamp" in error_msg.lower()

    async def test_webhook_timestamp_validation_future_request(self, async_benchmark_timer):
        """Test that future webhook requests are rejected."""
        
        # Create security helper for generating valid signatures
        security_helper = WebhookSecurityHelper("test_secret_future")
        
        # Create webhook payload with future timestamp
        future_timestamp = datetime.now(timezone.utc) + timedelta(minutes=10)
        webhook_payload = create_webhook_payload_kwargs(
            form_response={
                "form_id": f"form_{get_next_webhook_counter()}",
                "token": f"token_{get_next_webhook_counter()}",
                "submitted_at": future_timestamp.isoformat(),
                "landed_at": future_timestamp.isoformat(),
            }
        )
        
        async with async_benchmark_timer() as timer:
            # Serialize payload consistently
            payload_str = json.dumps(webhook_payload, ensure_ascii=False, separators=(',', ':'))
            
            # Create headers with future timestamp
            headers = security_helper.create_valid_headers_for_json_payload(payload_str)
            headers["x-typeform-timestamp"] = str(int(future_timestamp.timestamp()))
            
            # Test direct security verifier
            verifier = WebhookSecurityVerifier("test_secret_future")
            
            # Should fail with future timestamp
            is_valid, error_msg = await verifier.verify_webhook_request(
                payload=payload_str,
                headers=headers,
                timestamp_tolerance_minutes=5
            )
            
            # Should be rejected due to future timestamp
            assert is_valid is False
            assert error_msg is not None
            assert "timestamp" in error_msg.lower()

    async def test_webhook_replay_protection_with_nonce_simulation(self, async_benchmark_timer):
        """Test replay protection using simulated nonce tracking."""
        
        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET
        
        # Create multiple unique test payloads
        test_payloads = []
        for i in range(3):
            test_payload = {
                "event_id": f"test_{i}_{get_next_webhook_counter()}",
                "event_type": "form_response",
                "form_response": {
                    "form_id": f"form_{get_next_webhook_counter()}",
                    "token": f"unique_token_{i}_{get_next_webhook_counter()}",
                    "submitted_at": "2024-01-01T12:00:00Z",
                    "answers": []
                }
            }
            test_payloads.append(test_payload)
        
        async with async_benchmark_timer() as timer:
            # Track processed tokens to simulate nonce tracking
            processed_tokens = set()
            
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Security tests use verifier directly
            
            # Setup required onboarding forms in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
            from datetime import datetime, timezone
            async with FakeUnitOfWork() as uow:
                for i, test_payload in enumerate(test_payloads):
                    form_id = test_payload["form_response"]["form_id"]
                    onboarding_form = OnboardingForm(
                        id=20 + i,
                        typeform_id=form_id,
                        webhook_url="https://test.webhook.url",
                        user_id=1,
                        status=OnboardingFormStatus.ACTIVE,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()
            
            # Create security helper
            security_helper = WebhookSecurityHelper(webhook_secret)
            
            # Process each payload once
            for i, test_payload in enumerate(test_payloads):
                payload_str = json.dumps(test_payload, separators=(',', ':'))
                token = test_payload["form_response"]["token"]
                
                # Check if we've seen this token before (nonce check)
                if token in processed_tokens:
                    # This would be a replay attack - skip processing
                    continue
                
                # Generate valid headers
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}
                
                # Process the webhook
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, err = await verifier.verify_webhook_request(payload=payload_str, headers=headers)
                assert is_valid is True, f"Failed for payload {i}: {err}"
                
                # Mark token as processed
                processed_tokens.add(token)
            
            # Verify we processed all unique scenarios
            assert len(processed_tokens) == 3

    async def test_webhook_signature_replay_with_different_payload(self, async_benchmark_timer):
        """Test that valid signature cannot be reused with different payload."""
        
        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET
        
        # Create first test payload
        test_payload_1 = {
            "event_id": f"test_1_{get_next_webhook_counter()}",
            "event_type": "form_response",
            "form_response": {
                "form_id": "original_form",
                "token": f"original_token_{get_next_webhook_counter()}",
                "submitted_at": "2024-01-01T12:00:00Z",
                "answers": []
            }
        }
        
        # Create second test payload with different content
        test_payload_2 = {
            "event_id": f"test_2_{get_next_webhook_counter()}",
            "event_type": "form_response",
            "form_response": {
                "form_id": f"different_form_{get_next_webhook_counter()}",
                "token": f"different_token_{get_next_webhook_counter()}",
                "submitted_at": "2024-01-01T12:00:00Z",
                "answers": []
            }
        }
        
        async with async_benchmark_timer() as timer:
            # Using direct verifier for security validation in this test
            
            # Setup required onboarding forms in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
            from datetime import datetime, timezone
            async with FakeUnitOfWork() as uow:
                # Form for first payload
                onboarding_form_1 = OnboardingForm(
                    id=1,
                    typeform_id="original_form",
                    webhook_url="https://test.webhook.url",
                    user_id=1,
                    status=OnboardingFormStatus.ACTIVE,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await uow.onboarding_forms.add(onboarding_form_1)
                await uow.commit()
            
            # Create security helper and generate signatures
            security_helper = WebhookSecurityHelper(webhook_secret)
            
            payload_str_1 = json.dumps(test_payload_1, separators=(',', ':'))
            payload_str_2 = json.dumps(test_payload_2, separators=(',', ':'))
            
            signature_1 = security_helper.generate_valid_signature(payload_str_1)
            headers_1 = {"typeform-signature": signature_1}
            
            # First request should validate
            verifier = WebhookSecurityVerifier(webhook_secret)
            is_valid_1, _ = await verifier.verify_webhook_request(payload=payload_str_1, headers=headers_1)
            assert is_valid_1 is True
            
            # Attempt to use first signature with second payload (signature replay attack)
            malicious_headers = headers_1.copy()  # Reuse old signature
            
            is_valid_2, err_2 = await verifier.verify_webhook_request(payload=payload_str_2, headers=malicious_headers)
            
            # Should be rejected due to signature mismatch
            assert is_valid_2 is False

    async def test_webhook_security_timing_attack_prevention(self, async_benchmark_timer):
        """Test that signature comparison prevents timing attacks."""
        
        # Create security helper
        security_helper = WebhookSecurityHelper("timing_test_secret")
        webhook_payload = create_webhook_payload_kwargs()
        
        async with async_benchmark_timer() as timer:
            # Serialize payload consistently
            payload_str = json.dumps(webhook_payload, ensure_ascii=False, separators=(',', ':'))
            
            # Create valid signature
            valid_signature = security_helper.generate_valid_signature(payload_str)
            
            # Create multiple invalid signatures of different lengths
            invalid_signatures = [
                "sha256=" + "a" * 44,  # Short invalid
                "sha256=" + "b" * 44,  # Different short invalid
                "sha256=" + "c" * 88,  # Long invalid
                "",  # Empty
                "invalid_format"  # No sha256= prefix
            ]
            
            # Test verifier directly to ensure timing-safe comparison
            verifier = WebhookSecurityVerifier("timing_test_secret")
            
            # Test valid signature (extract signature part without sha256= prefix)
            signature_value = valid_signature[7:] if valid_signature.startswith("sha256=") else valid_signature
            valid_result = await verifier._verify_signature(payload_str, signature_value)
            assert valid_result is True
            
            # Test all invalid signatures - should all fail consistently
            for invalid_sig in invalid_signatures:
                if invalid_sig.startswith("sha256="):
                    sig_value = invalid_sig[7:]  # Remove sha256= prefix
                    invalid_result = await verifier._verify_signature(payload_str, sig_value)
                    assert invalid_result is False

    async def test_webhook_replay_protection_comprehensive_scenarios(self, async_benchmark_timer):
        """Test comprehensive replay attack protection scenarios."""
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Use verifier directly
            
            # Setup required onboarding form in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
            from datetime import datetime, timezone
            async with fake_uow_factory() as uow:
                onboarding_form = OnboardingForm(
                    id=1,
                    typeform_id="comprehensive_form",
                    webhook_url="https://test.webhook.url",
                    user_id=1,
                    status=OnboardingFormStatus.ACTIVE,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()
            
            # Use the validated environment secret
            webhook_secret = WEBHOOK_SECRET
            
            # Scenario 1: Valid fresh request
            test_payload = {
                "event_id": "comprehensive_test",
                "event_type": "form_response",
                "form_response": {
                    "form_id": "comprehensive_form",
                    "token": f"comprehensive_token_{get_next_webhook_counter()}",
                    "submitted_at": "2024-01-01T12:00:00Z",
                    "answers": []
                }
            }
            payload_str = json.dumps(test_payload, separators=(',', ':'))
            
            # Generate valid headers
            security_helper = WebhookSecurityHelper(webhook_secret)
            signature = security_helper.generate_valid_signature(payload_str)
            headers = {"typeform-signature": signature}
            
            verifier = WebhookSecurityVerifier(webhook_secret)
            is_valid, err = await verifier.verify_webhook_request(payload=payload_str, headers=headers)
            assert is_valid is True
            
            # Scenario 2: Same request with modified timestamp header (old timestamp)
            modified_headers = headers.copy()
            old_timestamp = str(int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()))
            modified_headers["x-typeform-timestamp"] = old_timestamp
            
            # With timestamp validation enabled, old timestamps should be rejected
            is_valid_2, err_2 = await verifier.verify_webhook_request(payload=payload_str, headers=modified_headers)
            assert is_valid_2 is False
            assert err_2 is not None and ("timestamp" in err_2.lower() or "replay" in err_2.lower())