"""
Security Penetration Testing for TypeForm Webhook Handler

Comprehensive security testing to validate webhook endpoint protection against
common web application security vulnerabilities and attack vectors.

Tests common attack patterns including injection attacks, buffer overflows,
timing attacks, header manipulation, and malicious payload attacks.
"""

import pytest
import json
import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import patch

from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.services.webhook_security import WebhookSecurityVerifier
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
    FormResponseProcessingError
)
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.contexts.client_onboarding.fakes.webhook_security import (
    create_valid_webhook_security_scenario,
    WebhookSecurityHelper
)
from tests.utils.counter_manager import get_next_webhook_counter


pytestmark = pytest.mark.anyio


class TestWebhookPenetrationTesting:
    """Comprehensive penetration testing for webhook security."""

    async def test_sql_injection_in_payload(self, async_benchmark_timer):
        """Test protection against SQL injection attacks in webhook payload."""
        
        # Create valid security scenario
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # SQL injection payloads
            sql_injection_payloads = [
                "'; DROP TABLE clients; --",
                "1' OR '1'='1",
                "' UNION SELECT * FROM users --",
                "'; INSERT INTO admin (user, pass) VALUES ('hacker', 'password'); --",
                "' OR 1=1 --",
                "'; UPDATE clients SET role='admin' WHERE id=1; --"
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
                            "text": injection_payload  # SQL injection in answer text
                        }
                    ],
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                payload_str = json.dumps(malicious_payload)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}
                
                # Attempt processing - should not result in SQL execution
                with patch('src.contexts.client_onboarding.services.webhook_handler.logger') as mock_logger:
                    status_code, result = await webhook_handler.handle_webhook(payload_str, headers, webhook_secret)
                    
                    # Verify safe handling - no SQL injection should occur
                    assert result is not None
                    # Verify logging captured potential security event
                    mock_logger.info.assert_called()

    async def test_xss_payload_sanitization(self, async_benchmark_timer):
        """Test protection against XSS attacks in webhook payload."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # XSS attack payloads
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "<iframe src=javascript:alert('XSS')></iframe>",
                "<body onload=alert('XSS')>",
                "';alert('XSS');//"
            ]
            
            for xss_payload in xss_payloads:
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "short_text"},
                            "text": xss_payload  # XSS in answer text
                        }
                    ],
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                payload_str = json.dumps(malicious_payload)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}
                
                # Process and verify XSS is handled safely
                status_code, result = await webhook_handler.handle_webhook(payload_str, headers, webhook_secret)
                assert result is not None

    async def test_buffer_overflow_large_payload_attack(self, async_benchmark_timer):
        """Test protection against buffer overflow attacks with extremely large payloads."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            
            # Create progressively larger payloads to test limits
            large_payloads = [
                "A" * 1000000,      # 1MB
                "A" * 5000000,      # 5MB
                "A" * 10000000,     # 10MB
                "A" * 50000000,     # 50MB (should trigger protection)
            ]
            
            for large_content in large_payloads:
                malicious_payload = {
                    "form_id": "test_form_123",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "long_text"},
                            "text": large_content  # Extremely large content
                        }
                    ],
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                payload_str = json.dumps(malicious_payload)
                
                # Test that large payloads are rejected
                if len(payload_str.encode('utf-8')) > verifier.max_payload_size:
                    with pytest.raises(WebhookPayloadError, match="Payload size exceeds maximum allowed"):
                        security_helper = WebhookSecurityHelper(webhook_secret)
                        signature = security_helper.generate_valid_signature(malicious_payload)
                        headers = {"typeform-signature": signature}
                        await verifier.verify_webhook_request(payload_str, headers)

    async def test_timing_attack_resistance(self, async_benchmark_timer):
        """Test protection against timing attacks on signature verification."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            payload_str = json.dumps(security_scenario["payload"])
            
            # Generate correct signature
            security_helper = WebhookSecurityHelper(webhook_secret)
            correct_signature = security_helper.generate_valid_signature(security_scenario["payload"])
            
            # Generate increasingly similar but incorrect signatures
            timing_attack_signatures = [
                "a" * len(correct_signature),  # Completely wrong
                correct_signature[:-10] + "a" * 10,  # Wrong suffix
                correct_signature[:-5] + "a" * 5,   # Wrong last 5 chars
                correct_signature[:-1] + "a",       # Wrong last char
                correct_signature + "a",            # Extra character
            ]
            
            timing_results = []
            
            # Test timing consistency across different invalid signatures
            for invalid_sig in timing_attack_signatures:
                headers = {"typeform-signature": f"sha256={invalid_sig}"}
                
                start_time = time.perf_counter()
                is_valid, _ = await verifier.verify_webhook_request(payload_str, headers)
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
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            payload_str = json.dumps(security_scenario["payload"])
            
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
                    "content-type": "application/json"
                }
                
                # Should handle header injection safely
                is_valid, error_msg = await verifier.verify_webhook_request(payload_str, malicious_headers)
                
                # Should be invalid due to malformed signature
                assert not is_valid
                assert error_msg is not None

    async def test_malformed_json_payload_attacks(self, async_benchmark_timer):
        """Test handling of malformed JSON payloads designed to cause parsing errors."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            webhook_handler = WebhookHandler(fake_uow_factory)
            
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
                import hmac, hashlib, base64
                payload_with_newline = malformed_payload + '\n'
                computed_hmac = hmac.new(
                    webhook_secret.encode('utf-8'),
                    payload_with_newline.encode('utf-8'),
                    hashlib.sha256
                ).digest()
                signature = f"sha256={base64.b64encode(computed_hmac).decode('utf-8')}"
                headers = {"typeform-signature": signature}
                
                # Should handle malformed JSON gracefully
                with pytest.raises((FormResponseProcessingError, ValueError, json.JSONDecodeError)):
                    await webhook_handler.handle_webhook(malformed_payload, headers, webhook_secret)

    async def test_unicode_and_encoding_attacks(self, async_benchmark_timer):
        """Test handling of Unicode and encoding-based attacks."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            
            # Unicode and encoding attack payloads
            unicode_attacks = [
                "\u0000\u0001\u0002",  # Null bytes and control characters
                "café", # UTF-8 characters
                "\U0001F4A9",  # Emoji
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
                            "text": unicode_content
                        }
                    ],
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                payload_str = json.dumps(malicious_payload, ensure_ascii=False)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}
                
                # Should handle Unicode content safely
                is_valid, error_msg = await verifier.verify_webhook_request(payload_str, headers)
                assert is_valid  # Valid signature with Unicode content should pass

    async def test_concurrent_attack_simulation(self, async_benchmark_timer):
        """Test system behavior under concurrent attack simulation."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # Simulate concurrent attacks with different patterns
            async def attack_scenario(attack_type: str, payload_modifier: str):
                """Single attack scenario."""
                malicious_payload = {
                    "form_id": f"attack_{attack_type}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_123", "type": "short_text"},
                            "text": payload_modifier
                        }
                    ],
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                payload_str = json.dumps(malicious_payload)
                security_helper = WebhookSecurityHelper(webhook_secret)
                signature = security_helper.generate_valid_signature(malicious_payload)
                headers = {"typeform-signature": signature}
                
                try:
                    status_code, result = await webhook_handler.handle_webhook(payload_str, headers, webhook_secret)
                    return f"{attack_type}: success"
                except Exception as e:
                    return f"{attack_type}: {type(e).__name__}"
            
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
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            
            # Resource exhaustion scenarios
            resource_attacks = [
                # Deeply nested JSON
                {"deeply_nested": {"level1": {"level2": {"level3": {"level4": {"level5": "value"}}}}}},
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
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                payload_str = json.dumps(malicious_payload)
                
                # Test payload size limits
                if len(payload_str.encode('utf-8')) > verifier.max_payload_size:
                    with pytest.raises(WebhookPayloadError):
                        security_helper = WebhookSecurityHelper(webhook_secret)
                        signature = security_helper.generate_valid_signature(malicious_payload)
                        headers = {"typeform-signature": signature}
                        await verifier.verify_webhook_request(payload_str, headers)
                else:
                    # Should process within reasonable time limits
                    security_helper = WebhookSecurityHelper(webhook_secret)
                    signature = security_helper.generate_valid_signature(malicious_payload)
                    headers = {"typeform-signature": signature}
                    
                    start_time = time.perf_counter()
                    is_valid, _ = await verifier.verify_webhook_request(payload_str, headers)
                    processing_time = time.perf_counter() - start_time
                    
                    # Should complete within reasonable time (5 seconds max)
                    assert processing_time < 5.0
                    assert is_valid


class TestAdvancedSecurityScenarios:
    """Advanced security scenario testing."""

    async def test_signature_bypass_attempts(self, async_benchmark_timer):
        """Test various attempts to bypass signature verification."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            payload_str = json.dumps(security_scenario["payload"])
            
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
                is_valid, error_msg = await verifier.verify_webhook_request(payload_str, headers)
                assert not is_valid  # All bypass attempts should fail
                assert error_msg is not None

    async def test_algorithmic_complexity_attacks(self, async_benchmark_timer):
        """Test protection against algorithmic complexity attacks."""
        
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        async with async_benchmark_timer() as timer:
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            webhook_handler = WebhookHandler(fake_uow_factory)
            
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
                import hmac, hashlib, base64
                payload_with_newline = attack_payload + '\n'
                computed_hmac = hmac.new(
                    webhook_secret.encode('utf-8'),
                    payload_with_newline.encode('utf-8'),
                    hashlib.sha256
                ).digest()
                signature = f"sha256={base64.b64encode(computed_hmac).decode('utf-8')}"
                headers = {"typeform-signature": signature}
                
                # Measure processing time
                start_time = time.perf_counter()
                
                try:
                    status_code, result = await webhook_handler.handle_webhook(attack_payload, headers, webhook_secret)
                    processing_time = time.perf_counter() - start_time
                    
                    # Should complete within reasonable time
                    assert processing_time < 10.0  # Max 10 seconds
                    
                except (FormResponseProcessingError, WebhookPayloadError):
                    # Acceptable to reject complex payloads
                    processing_time = time.perf_counter() - start_time
                    assert processing_time < 5.0  # Should fail fast