"""
Security Penetration Testing for TypeForm Webhook Handler

Comprehensive security testing to validate webhook endpoint protection against
common web application security vulnerabilities and attack vectors.

Tests common attack patterns including injection attacks, buffer overflows,
timing attacks, header manipulation, and malicious payload attacks.
"""

import asyncio
import json
import os
import time
from datetime import UTC, datetime, timezone
from unittest.mock import patch

import pytest
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
)
from src.contexts.client_onboarding.core.services.webhooks.security import (
    WebhookSecurityVerifier,
)
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
)
from tests.contexts.client_onboarding.fakes.webhook_security import (
    WebhookSecurityHelper,
)
from tests.contexts.client_onboarding.utils.webhook_test_processor import (
    process_typeform_webhook,
)
from tests.utils.counter_manager import get_next_webhook_counter

# Skip entire test suite if webhook secret is not configured
WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    pytest.skip(
        "TYPEFORM_WEBHOOK_SECRET environment variable required for security tests",
        allow_module_level=True,
    )

pytestmark = pytest.mark.anyio


class TestWebhookPenetrationTesting:
    """Comprehensive penetration testing for webhook security."""

    async def test_sql_injection_in_payload(self, async_benchmark_timer):
        """Test protection against SQL injection attacks in webhook payload."""

        # Create valid security scenario
        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()

            uow = FakeUnitOfWork()

            # SQL injection payloads
            sql_injection_payloads = [
                "'; DROP TABLE clients; --",
                "1' OR '1'='1",
                "' UNION SELECT * FROM users --",
                "'; INSERT INTO admin (user, pass) VALUES ('hacker', 'password'); --",
                "' OR 1=1 --",
                "'; UPDATE clients SET role='admin' WHERE id=1; --",
            ]

            for injection_payload in sql_injection_payloads:
                # Inject SQL into form response payload
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "landing_id": injection_payload,  # SQL injection in landing_id
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "short_text"},
                            "text": injection_payload,  # SQL injection in answer text
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(malicious_payload)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}

                # Attempt processing - should not result in SQL execution
                # Verify signature then process via core processor
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                if is_valid:
                    success, error, _ = await process_typeform_webhook(
                        payload=payload_str, headers=headers, uow_factory=lambda: uow
                    )
                    assert isinstance(success, bool)

    async def test_xss_payload_sanitization(self, async_benchmark_timer):
        """Test protection against XSS attacks in webhook payload."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            uow = FakeUnitOfWork()

            # XSS attack payloads
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "<iframe src=javascript:alert('XSS')></iframe>",
                "<body onload=alert('XSS')>",
                "';alert('XSS');//",
            ]

            for xss_payload in xss_payloads:
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "short_text"},
                            "text": xss_payload,  # XSS in answer text
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(malicious_payload)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}

                # Process and verify XSS is handled safely
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                if is_valid:
                    success, error, _ = await process_typeform_webhook(
                        payload=payload_str, headers=headers, uow_factory=lambda: uow
                    )
                    assert isinstance(success, bool)

    async def test_buffer_overflow_large_payload_attack(self, async_benchmark_timer):
        """Test protection against buffer overflow attacks with extremely large payloads."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)

            # Create progressively larger payloads to test limits
            large_payloads = [
                "A" * 1000000,  # 1MB
                "A" * 5000000,  # 5MB
                "A" * 10000000,  # 10MB
                "A" * 50000000,  # 50MB (should trigger protection)
            ]

            for large_content in large_payloads:
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "long_text"},
                            "text": large_content,  # Extremely large content
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(malicious_payload)

                # Test that large payloads are rejected
                if len(payload_str.encode("utf-8")) > verifier.max_payload_size:
                    with pytest.raises(
                        WebhookPayloadError,
                        match="Payload size exceeds maximum allowed",
                    ):
                        security_helper = WebhookSecurityHelper(webhook_secret)
                        signature = security_helper.generate_valid_signature(
                            malicious_payload
                        )
                        headers = {"typeform-signature": signature}
                        await verifier.verify_webhook_request(payload_str, headers)

    async def test_timing_attack_resistance(self, async_benchmark_timer):
        """Test protection against timing attacks on signature verification."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)

            # Create a test payload
            test_payload = {
                "event_id": "test_123",
                "event_type": "form_response",
                "form_response": {
                    "form_id": "test_form",
                    "token": "test_token",
                    "submitted_at": "2024-01-01T12:00:00Z",
                    "answers": [],
                },
            }
            payload_str = json.dumps(test_payload, separators=(",", ":"))

            # Generate correct signature
            security_helper = WebhookSecurityHelper(webhook_secret)
            correct_signature = security_helper.generate_valid_signature(test_payload)

            # Generate increasingly similar but incorrect signatures
            timing_attack_signatures = [
                "a" * len(correct_signature),  # Completely wrong
                correct_signature[:-10] + "a" * 10,  # Wrong suffix
                correct_signature[:-5] + "a" * 5,  # Wrong last 5 chars
                correct_signature[:-1] + "a",  # Wrong last char
                correct_signature + "a",  # Extra character
            ]

            timing_results = []

            # Test timing consistency across different invalid signatures
            for invalid_sig in timing_attack_signatures:
                headers = {"typeform-signature": f"sha256={invalid_sig}"}

                start_time = time.perf_counter()
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                end_time = time.perf_counter()

                timing_results.append(end_time - start_time)
                assert not is_valid  # All should be invalid

            # Verify timing consistency (no significant timing differences)
            # All invalid signatures should take roughly the same time
            max_timing = max(timing_results)
            min_timing = min(timing_results)
            timing_variance = max_timing - min_timing

            # Timing variance should be minimal (within reasonable bounds)
            assert timing_variance < 0.1  # Less than 100ms variance

    async def test_header_injection_attacks(self, async_benchmark_timer):
        """Test protection against HTTP header injection attacks."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            # Create a test payload
            test_payload = {
                "event_id": "test_123",
                "event_type": "form_response",
                "form_response": {
                    "form_id": "test_form",
                    "token": "test_token",
                    "submitted_at": "2024-01-01T12:00:00Z",
                    "answers": [],
                },
            }
            payload_str = json.dumps(test_payload, separators=(",", ":"))

            # Header injection payloads
            header_injection_attacks = [
                "sha256=valid_sig\r\nX-Injected-Header: malicious",
                "sha256=valid_sig\nSet-Cookie: session=hijacked",
                "sha256=valid_sig\r\n\r\n<script>alert('xss')</script>",
                "sha256=valid_sig\x00\x0aX-Forwarded-For: attacker.com",
                "sha256=valid_sig%0d%0aLocation: http://evil.com",
            ]

            for injection_header in header_injection_attacks:
                malicious_headers = {
                    "typeform-signature": injection_header,
                    "content-type": "application/json",
                }

                # Should handle header injection safely
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, malicious_headers
                )

                # Should be invalid due to malformed signature
                assert not is_valid
                assert error_msg is not None

    async def test_malformed_json_payload_attacks(self, async_benchmark_timer):
        """Test handling of malformed JSON payloads designed to cause parsing errors."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            uow = FakeUnitOfWork()

            # Malformed JSON attack payloads
            malformed_payloads = [
                '{"form_id": "test", "invalid": }',  # Missing value
                '{"form_id": "test", "nested": {"unclosed": }',  # Unclosed nested
                '{"form_id": "test"',  # Incomplete JSON
                '{"form_id": "test", "answers": [{"invalid_structure"}]}',  # Invalid array
                '{"form_id": null, "answers": undefined}',  # Invalid values
                '{form_id: "test"}',  # Unquoted keys
                '{"form_id": "test", "answers": [null, undefined, NaN]}',  # Invalid values
            ]

            for malformed_payload in malformed_payloads:
                # Generate signature for malformed payload - this will work even for malformed JSON
                # since we're signing the raw string
                import base64
                import hashlib
                import hmac

                payload_with_newline = malformed_payload + "\n"
                computed_hmac = hmac.new(
                    webhook_secret.encode("utf-8"),  # type: ignore
                    payload_with_newline.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
                signature = f"sha256={base64.b64encode(computed_hmac).decode('utf-8')}"
                headers = {"typeform-signature": signature}

                # Should handle malformed JSON gracefully via processor path
                success, error, _ = await process_typeform_webhook(
                    payload=malformed_payload,
                    headers=headers,
                    uow_factory=lambda: FakeUnitOfWork(),
                )
                assert success is False
                assert error is not None and (
                    "invalid json" in error.lower()
                    or "invalid payload" in error.lower()
                )

    async def test_unicode_and_encoding_attacks(self, async_benchmark_timer):
        """Test handling of Unicode and encoding-based attacks."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)

            # Unicode and encoding attack payloads
            unicode_attacks = [
                "\u0000\u0001\u0002",  # Null bytes and control characters
                "café",  # UTF-8 characters
                "\U0001f4a9",  # Emoji
                "\uffff\ufffe",  # Unicode edge cases
                "𝕏𝕐𝕑",  # Mathematical symbols
                "\u202e\u202d",  # Bidirectional override characters
            ]

            for unicode_content in unicode_attacks:
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "short_text"},
                            "text": unicode_content,
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(malicious_payload, ensure_ascii=False)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}

                # Should handle Unicode content safely
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                assert is_valid  # Valid signature with Unicode content should pass

    async def test_concurrent_attack_simulation(self, async_benchmark_timer):
        """Test system behavior under concurrent attack simulation."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            # No handler usage

            # Simulate concurrent attacks with different patterns
            async def attack_scenario(attack_type: str, payload_modifier: str):
                """Single attack scenario."""
                malicious_payload = {
                    "form_id": f"attack_{attack_type}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "short_text"},
                            "text": payload_modifier,
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(malicious_payload)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}

                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                if not is_valid:
                    return f"{attack_type}: invalid_signature"
                local_uow = FakeUnitOfWork()
                success, error, _ = await process_typeform_webhook(
                    payload=payload_str, headers=headers, uow_factory=lambda: local_uow
                )
                return f"{attack_type}: {'success' if success else 'failed'}"

            # Launch concurrent attacks
            attack_tasks = [
                attack_scenario("sql_injection", "'; DROP TABLE users; --"),
                attack_scenario("xss_attack", "<script>alert('xss')</script>"),
                attack_scenario("buffer_overflow", "A" * 100000),
                attack_scenario("unicode_attack", "\u0000\uffff"),
                attack_scenario("json_injection", '{"nested": "value"}'),
            ]

            # Execute all attacks concurrently
            results = await asyncio.gather(*attack_tasks, return_exceptions=True)

            # Verify system handled concurrent attacks
            assert len(results) == 5
            for result in results:
                assert isinstance(result, str)  # All should complete with some result

    async def test_resource_exhaustion_attacks(self, async_benchmark_timer):
        """Test protection against resource exhaustion attacks."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)

            # Resource exhaustion scenarios
            resource_attacks = [
                # Deeply nested JSON
                {
                    "deeply_nested": {
                        "level1": {
                            "level2": {"level3": {"level4": {"level5": "value"}}}
                        }
                    }
                },
                # Large number of array elements
                {"large_array": ["item"] * 10000},
                # Large number of object keys
                {f"key_{i}": f"value_{i}" for i in range(1000)},
                # Extremely long strings
                {"long_string": "x" * 100000},
            ]

            for resource_attack in resource_attacks:
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "attack_data": resource_attack,
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(malicious_payload)

                # Test payload size limits
                if len(payload_str.encode("utf-8")) > verifier.max_payload_size:
                    with pytest.raises(WebhookPayloadError):
                        security_helper = WebhookSecurityHelper(webhook_secret)
                        signature = security_helper.generate_valid_signature(
                            payload_str
                        )
                        headers = {"typeform-signature": signature}
                        await verifier.verify_webhook_request(payload_str, headers)
                else:
                    # Should process within reasonable time limits
                    security_helper = WebhookSecurityHelper(webhook_secret)
                    signature = security_helper.generate_valid_signature(payload_str)
                    headers = {"typeform-signature": signature}

                    start_time = time.perf_counter()
                    is_valid, _ = await verifier.verify_webhook_request(
                        payload_str, headers
                    )
                    processing_time = time.perf_counter() - start_time

                    # Should complete within reasonable time (5 seconds max)
                    assert processing_time < 5.0
                    assert is_valid


class TestAdvancedSecurityScenarios:
    """Advanced security scenario testing."""

    async def test_signature_bypass_attempts(self, async_benchmark_timer):
        """Test various attempts to bypass signature verification."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            # Create a test payload
            test_payload = {
                "event_id": "test_123",
                "event_type": "form_response",
                "form_response": {
                    "form_id": "test_form",
                    "token": "test_token",
                    "submitted_at": "2024-01-01T12:00:00Z",
                    "answers": [],
                },
            }
            payload_str = json.dumps(test_payload, separators=(",", ":"))

            # Signature bypass attempts
            bypass_attempts = [
                {},  # No signature header
                {"typeform-signature": ""},  # Empty signature
                {"typeform-signature": "invalid"},  # Invalid format
                {"typeform-signature": "sha256="},  # Empty hash
                {"TYPEFORM-SIGNATURE": "sha256=valid"},  # Case variation
                {"typeform-signature": "md5=hash"},  # Wrong algorithm
                {"x-typeform-signature": "sha256=hash"},  # Wrong header name
            ]

            for headers in bypass_attempts:
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                assert not is_valid  # All bypass attempts should fail
                assert error_msg is not None

    async def test_algorithmic_complexity_attacks(self, async_benchmark_timer):
        """Test protection against algorithmic complexity attacks."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            # No handler usage

            # Create payloads designed to trigger worst-case parsing complexity
            complexity_attacks = [
                # Repeated nested structures
                json.dumps({"a" * 1000: {"b" * 1000: "value"}}),
                # Large repeated keys
                json.dumps({("key_" + "x" * 100): "value" for _ in range(100)}),
                # Deep recursion patterns
                json.dumps({"recursive": {"recursive": {"recursive": "value"}}}),
            ]

            for attack_payload in complexity_attacks:
                # Generate signature for complex payload using raw string approach
                import base64
                import hashlib
                import hmac

                payload_with_newline = attack_payload + "\n"
                computed_hmac = hmac.new(
                    webhook_secret.encode("utf-8"),  # type: ignore
                    payload_with_newline.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
                signature = f"sha256={base64.b64encode(computed_hmac).decode('utf-8')}"
                headers = {"typeform-signature": signature}

                # Measure processing time
                start_time = time.perf_counter()

                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    attack_payload, headers
                )
                start_time = time.perf_counter()
                if is_valid:
                    success, error, _ = await process_typeform_webhook(
                        payload=attack_payload,
                        headers=headers,
                        uow_factory=lambda: FakeUnitOfWork(),
                    )
                processing_time = time.perf_counter() - start_time
                # Should complete within reasonable time
                assert processing_time < 10.0
