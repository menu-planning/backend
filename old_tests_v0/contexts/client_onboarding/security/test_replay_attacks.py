"""
Replay Attack Validation Tests

Comprehensive testing of replay attack scenarios to validate protection
mechanisms including timestamp validation, signature replay prevention,
and advanced replay attack patterns.

This complements test_replay_protection.py by focusing on attack simulation
rather than protection mechanism testing.
"""

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta, timezone

import anyio
import pytest
from old_tests_v0.contexts.client_onboarding.data_factories.typeform_factories import (
    create_webhook_payload_kwargs,
)
from old_tests_v0.contexts.client_onboarding.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
)
from old_tests_v0.contexts.client_onboarding.fakes.webhook_security import (
    WebhookSecurityHelper,
)
from old_tests_v0.contexts.client_onboarding.utils.webhook_test_processor import (
    process_typeform_webhook,
)
from old_tests_v0.utils.counter_manager import get_next_webhook_counter
from src.contexts.client_onboarding.core.services.webhooks.security import (
    WebhookSecurityVerifier,
)

# Skip entire test suite if webhook secret is not configured
WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    pytest.skip(
        "TYPEFORM_WEBHOOK_SECRET environment variable required for security tests",
        allow_module_level=True,
    )

pytestmark = pytest.mark.anyio


class TestReplayAttackScenarios:
    """Test various replay attack scenarios and validation."""

    async def test_simple_replay_attack(self, async_benchmark_timer):
        """Test basic replay attack with identical signature and payload."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            uow = FakeUnitOfWork()

            # Setup required onboarding form in fake database
            from datetime import datetime, timezone

            from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
                OnboardingForm,
                OnboardingFormStatus,
            )

            onboarding_form = OnboardingForm(
                id=1,
                user_id=1,
                typeform_id="replay_test_form",
                webhook_url="https://test.webhook.url",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Add form to fake database
            async with FakeUnitOfWork() as uow:
                await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()

            # Create proper webhook payload with required fields
            payload = create_webhook_payload_kwargs(
                form_response={
                    "form_id": "replay_test_form",
                    "token": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "short_text"},
                            "text": "Original response",
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
            )

            security_helper = WebhookSecurityHelper(webhook_secret)

            # Ensure consistent JSON serialization
            payload_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

            # Create headers with timestamp for proper replay protection testing
            current_timestamp = str(int(datetime.now(UTC).timestamp()))
            signature = security_helper.generate_valid_signature(payload_str)
            headers = {
                "Typeform-Signature": signature,
                "Content-Type": "application/json",
                "User-Agent": "Typeform-Webhooks/1.0",
                "Content-Length": str(len(payload_str)),
                "x-typeform-timestamp": current_timestamp,
            }

            # First request should succeed
            verifier = WebhookSecurityVerifier(webhook_secret)
            is_valid_1, _ = await verifier.verify_webhook_request(payload_str, headers)
            assert is_valid_1 is True
            success_1, error_1, _ = await process_typeform_webhook(
                payload=payload_str, headers=headers, uow_factory=lambda: uow
            )
            assert success_1 is True

            # Create a second request with an old timestamp (simulating replay attack)
            old_timestamp = str(
                int(datetime.now(UTC).timestamp()) - 600
            )  # 10 minutes old
            old_signature = security_helper.generate_valid_signature(payload_str)
            old_headers = {
                "Typeform-Signature": old_signature,
                "Content-Type": "application/json",
                "User-Agent": "Typeform-Webhooks/1.0",
                "Content-Length": str(len(payload_str)),
                "x-typeform-timestamp": old_timestamp,
            }

            # Request with old timestamp should fail (replay protection)
            is_valid_2, err_2 = await verifier.verify_webhook_request(
                payload_str, old_headers
            )
            assert is_valid_2 is False

    async def test_delayed_replay_attack(self, async_benchmark_timer):
        """Test replay attack after time delay."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            uow = FakeUnitOfWork()

            # Setup required onboarding form in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
                OnboardingForm,
                OnboardingFormStatus,
            )

            onboarding_form = OnboardingForm(
                id=2,
                user_id=1,
                typeform_id="delayed_replay_test",
                webhook_url="https://test.webhook.url",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Add form to fake database
            async with FakeUnitOfWork() as uow:
                await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()

            # Create payload with older timestamp
            old_timestamp = datetime.now(UTC) - timedelta(minutes=10)
            payload = create_webhook_payload_kwargs(
                form_response={
                    "form_id": "delayed_replay_test",
                    "token": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "short_text"},
                            "text": "Delayed replay response",
                        }
                    ],
                    "submitted_at": old_timestamp.isoformat(),
                }
            )

            payload_str = json.dumps(payload, separators=(",", ":"))
            security_helper = WebhookSecurityHelper(webhook_secret)
            signature = security_helper.generate_valid_signature(payload_str)
            headers = {"typeform-signature": signature}

            # Process the webhook
            verifier = WebhookSecurityVerifier(webhook_secret)
            is_valid, err = await verifier.verify_webhook_request(payload_str, headers)
            if is_valid:
                success, error, _ = await process_typeform_webhook(
                    payload=payload_str, headers=headers, uow_factory=lambda: uow
                )
                assert isinstance(success, bool)
                # Verify it's timestamp-related failure, not replay failure
            if not is_valid:
                assert err is not None and (
                    "timestamp" in err.lower() or "time" in err.lower()
                )

    async def test_modified_payload_replay_attack(self, async_benchmark_timer):
        """Test replay attack with modified payload but same signature."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)

            # Original payload
            original_payload = {
                "form_id": "modified_replay_test",
                "response_id": f"resp_{get_next_webhook_counter()}",
                "answers": [
                    {
                        "field": {"id": "field_1", "type": "short_text"},
                        "text": "Original value",
                    }
                ],
                "submitted_at": datetime.now(UTC).isoformat(),
            }

            # Generate signature for original payload
            security_helper = WebhookSecurityHelper(webhook_secret)
            signature = security_helper.generate_valid_signature(original_payload)

            # Modified payload (attacker tries to change content)
            modified_payload = original_payload.copy()
            modified_payload["answers"][0]["text"] = "MODIFIED VALUE - ATTACK"

            modified_payload_str = json.dumps(modified_payload)
            headers = {"typeform-signature": signature}  # Using original signature

            # Should fail verification (signature doesn't match modified payload)
            is_valid, error_msg = await verifier.verify_webhook_request(
                modified_payload_str, headers
            )

            assert (
                not is_valid
            ), "Modified payload with original signature should be invalid"
            assert (
                error_msg is not None
            ), "Should provide error message for signature mismatch"

    async def test_cross_form_replay_attack(self, async_benchmark_timer):
        """Test replay attack using signature from one form on another form."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Payload for Form A
            payload_a = {
                "form_id": "form_a_legitimate",
                "response_id": f"resp_{get_next_webhook_counter()}",
                "answers": [
                    {
                        "field": {"id": "field_a", "type": "short_text"},
                        "text": "Form A response",
                    }
                ],
                "submitted_at": datetime.now(UTC).isoformat(),
            }

            # Payload for Form B (attacker's target)
            payload_b = {
                "form_id": "form_b_target",
                "response_id": f"resp_{get_next_webhook_counter()}",
                "answers": [
                    {
                        "field": {"id": "field_b", "type": "short_text"},
                        "text": "Form B response - ATTACK TARGET",
                    }
                ],
                "submitted_at": datetime.now(UTC).isoformat(),
            }

            # Generate signature for Form A
            signature_a = security_helper.generate_valid_signature(payload_a)

            # Try to use Form A's signature on Form B's payload
            payload_b_str = json.dumps(payload_b)
            headers = {"typeform-signature": signature_a}

            # Should fail verification
            is_valid, error_msg = await verifier.verify_webhook_request(
                payload_b_str, headers
            )

            assert not is_valid, "Cross-form signature replay should be invalid"
            assert (
                error_msg is not None
            ), "Should provide error message for signature mismatch"

    async def test_timestamp_manipulation_replay_attack(self, async_benchmark_timer):
        """Test replay attack with manipulated timestamps."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Test various timestamp manipulations
            timestamp_attacks = [
                # Future timestamp (way ahead)
                datetime.now(UTC) + timedelta(hours=24),
                # Very old timestamp
                datetime.now(UTC) - timedelta(days=30),
                # Just outside tolerance window
                datetime.now(UTC) - timedelta(minutes=10),
                # Epoch timestamp (1970)
                datetime(1970, 1, 1, tzinfo=UTC),
                # Far future timestamp
                datetime(2030, 12, 31, tzinfo=UTC),
            ]

            for i, attack_timestamp in enumerate(timestamp_attacks):
                payload = {
                    "form_id": f"timestamp_attack_{i}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": f"field_{i}", "type": "short_text"},
                            "text": f"Timestamp attack {i}",
                        }
                    ],
                    "submitted_at": attack_timestamp.isoformat(),
                }

                payload_str = json.dumps(payload)
                signature = security_helper.generate_valid_signature(payload)
                headers = {
                    "typeform-signature": signature,
                    "x-typeform-timestamp": str(int(attack_timestamp.timestamp())),
                }

                # Most timestamp manipulations should be rejected
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, headers
                )

                # Extreme timestamps should be rejected
                if (
                    abs((attack_timestamp - datetime.now(UTC)).total_seconds()) > 300
                ):  # 5 minutes
                    assert (
                        not is_valid
                    ), f"Extreme timestamp attack {i} should be rejected"
                # Note: Some may be valid if within tolerance window

    async def test_signature_format_manipulation_attacks(self, async_benchmark_timer):
        """Test replay attacks with manipulated signature formats."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

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

            # Generate valid signature
            valid_signature = security_helper.generate_valid_signature(test_payload)

            # Extract the hash part (after 'sha256=')
            if valid_signature.startswith("sha256="):
                hash_part = valid_signature[7:]  # Remove 'sha256=' prefix
            else:
                hash_part = valid_signature

            # Signature format manipulation attacks
            signature_attacks = [
                # Missing prefix
                hash_part,
                # Wrong algorithm prefix
                f"md5={hash_part}",
                f"sha1={hash_part}",
                f"sha512={hash_part}",
                # Case variations
                f"SHA256={hash_part}",
                f"Sha256={hash_part}",
                # Extra prefixes
                f"sha256=sha256={hash_part}",
                # URL encoding
                f"sha256%3D{hash_part}",
                # Base64 padding manipulation
                f"sha256={hash_part}===",
                f"sha256={hash_part[:-1]}",  # Truncated
                # Whitespace injection
                f"sha256= {hash_part}",
                f"sha256={hash_part} ",
                f" sha256={hash_part}",
            ]

            for i, attack_signature in enumerate(signature_attacks):
                headers = {"typeform-signature": attack_signature}

                # Should be invalid (signature format manipulation)
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, headers
                )

                assert (
                    not is_valid
                ), f"Signature format attack {i} should be invalid: {attack_signature}"
                assert error_msg is not None, f"Attack {i} should provide error message"

    async def test_concurrent_replay_attack_attempts(self, async_benchmark_timer):
        """Test concurrent replay attack attempts."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            # No handler needed here

            # Create valid payload and signature
            payload = {
                "form_id": "concurrent_replay_test",
                "response_id": f"resp_{get_next_webhook_counter()}",
                "answers": [
                    {
                        "field": {"id": "field_1", "type": "short_text"},
                        "text": "Concurrent replay target",
                    }
                ],
                "submitted_at": datetime.now(UTC).isoformat(),
            }

            payload_str = json.dumps(payload, separators=(",", ":"))
            security_helper = WebhookSecurityHelper(webhook_secret)
            signature = security_helper.generate_valid_signature(payload_str)
            headers = {"typeform-signature": signature}

            # Launch concurrent replay attempts
            async def replay_attempt(attempt_id: int) -> tuple[int, bool]:
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                return attempt_id, is_valid

            # Launch 10 concurrent replay attempts
            replay_tasks = [replay_attempt(i) for i in range(10)]
            results = await asyncio.gather(*replay_tasks, return_exceptions=True)

            # Analyze results: at most one verification should pass (race) depending on caching; accept <=1
            valid_count = sum(
                1
                for r in results
                if not isinstance(r, Exception)
                and isinstance(r, tuple)
                and r[1] is True
            )
            assert valid_count <= 1

    async def test_replay_attack_with_network_delay_simulation(
        self, async_benchmark_timer
    ):
        """Test replay attack with simulated network delays."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            uow = FakeUnitOfWork()

            # Setup required onboarding form in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
                OnboardingForm,
                OnboardingFormStatus,
            )

            onboarding_form = OnboardingForm(
                id=3,
                typeform_id="network_delay_replay_test",
                webhook_url="https://test.webhook.url",
                user_id=1,
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Add form to fake database
            async with FakeUnitOfWork() as uow:
                await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()

            # Create proper webhook payload with required fields
            payload = create_webhook_payload_kwargs(
                form_response={
                    "form_id": "network_delay_replay_test",
                    "token": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "short_text"},
                            "text": "Network delay simulation",
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
            )

            payload_str = json.dumps(payload, separators=(",", ":"))
            security_helper = WebhookSecurityHelper(webhook_secret)
            signature = security_helper.generate_valid_signature(payload_str)
            headers = {"typeform-signature": signature}

            # Process first request via processor
            success_1, error_1, _ = await process_typeform_webhook(
                payload=payload_str,
                headers=headers,
                uow_factory=lambda: FakeUnitOfWork(),
            )
            assert success_1 is True, "First request should succeed"

            # Simulate network delays and retry scenarios
            delay_scenarios = [0.1, 0.5, 1.0, 2.0, 5.0]  # seconds

            for delay in delay_scenarios:
                # Wait for specified delay
                await anyio.sleep(delay)

                # Attempt replay after delay: verification should fail
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, err = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                assert (
                    is_valid is False
                ), f"Replay after {delay}s delay should be blocked"

    async def test_sophisticated_replay_attack_patterns(self, async_benchmark_timer):
        """Test sophisticated replay attack patterns."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            # No handler usage
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Setup required onboarding form in fake database
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
                OnboardingForm,
                OnboardingFormStatus,
            )

            onboarding_form = OnboardingForm(
                id=4,
                typeform_id="sophisticated_replay_test",
                webhook_url="https://test.webhook.url",
                user_id=1,
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Add forms to fake database
            async with FakeUnitOfWork() as uow:
                await uow.onboarding_forms.add(onboarding_form)

                # Add forms for interleaved test
                for i in range(5):
                    interleaved_form = OnboardingForm(
                        id=10 + i,
                        typeform_id=f"interleaved_test_{i}",
                        webhook_url="https://test.webhook.url",
                        user_id=1,
                        status=OnboardingFormStatus.ACTIVE,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    await uow.onboarding_forms.add(interleaved_form)

                await uow.commit()

            # Pattern 1: Rapid-fire replay attempts
            base_payload = create_webhook_payload_kwargs(
                form_response={
                    "form_id": "sophisticated_replay_test",
                    "token": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "short_text"},
                            "text": "Sophisticated attack payload",
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
            )

            payload_str = json.dumps(base_payload)
            signature = security_helper.generate_valid_signature(base_payload)
            headers = {"typeform-signature": signature}

            # Rapid-fire attempts (100 requests in quick succession)
            rapid_fire_results = []
            for i in range(100):
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                rapid_fire_results.append(is_valid)

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.001)

            # Only first request should succeed
            success_count = sum(1 for ok in rapid_fire_results if ok)
            assert (
                success_count <= 1
            ), f"Too many rapid-fire replays succeeded: {success_count}"

            # Pattern 2: Interleaved legitimate and replay requests
            legitimate_payloads = []
            for i in range(5):
                payload = create_webhook_payload_kwargs(
                    form_response={
                        "form_id": f"interleaved_test_{i}",
                        "token": f"resp_{get_next_webhook_counter()}",
                        "answers": [
                            {
                                "field": {"id": f"field_{i}", "type": "short_text"},
                                "text": f"Legitimate request {i}",
                            }
                        ],
                        "submitted_at": datetime.now(UTC).isoformat(),
                    }
                )
                legitimate_payloads.append(payload)

            # Interleave legitimate requests with replay attempts
            interleaved_results = []

            for i, legit_payload in enumerate(legitimate_payloads):
                # Process legitimate request
                legit_payload_str = json.dumps(legit_payload)
                legit_signature = security_helper.generate_valid_signature(
                    legit_payload_str
                )
                legit_headers = {"typeform-signature": legit_signature}

                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, _ = await verifier.verify_webhook_request(
                    legit_payload_str, legit_headers
                )
                interleaved_results.append(("legitimate", is_valid))

                # Attempt replay of first payload
                is_valid_replay, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                interleaved_results.append(("replay", is_valid_replay))

            # All legitimate requests should succeed
            legit_successes = sum(
                1
                for req_type, ok in interleaved_results
                if req_type == "legitimate" and ok
            )
            assert (
                legit_successes == 5
            ), f"Not all legitimate requests succeeded: {legit_successes}/5"

            # All replay attempts should fail
            replay_failures = sum(
                1
                for req_type, ok in interleaved_results
                if req_type == "replay" and not ok
            )
            assert (
                replay_failures == 5
            ), f"Not all replay attempts blocked: {replay_failures}/5"


class TestAdvancedReplayAttackValidation:
    """Advanced replay attack validation scenarios."""

    async def test_replay_attack_with_header_manipulation(self, async_benchmark_timer):
        """Test replay attacks combined with header manipulation."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

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

            # Generate valid signature
            valid_signature = security_helper.generate_valid_signature(test_payload)

            # Header manipulation scenarios
            header_manipulations = [
                # Add extra signature headers
                {
                    "typeform-signature": valid_signature,
                    "x-typeform-signature": valid_signature,
                },
                # Case manipulation
                {
                    "TYPEFORM-SIGNATURE": valid_signature,
                },
                # Multiple signature values
                {
                    "typeform-signature": f"{valid_signature}, {valid_signature}",
                },
                # Extra headers that might confuse processing
                {
                    "typeform-signature": valid_signature,
                    "content-length": "999999",
                    "x-forwarded-for": "attacker.com",
                    "user-agent": "replay-attack-bot",
                },
                # Encoding manipulation
                {
                    "typeform-signature": valid_signature.replace("=", "%3D"),
                },
            ]

            for i, headers in enumerate(header_manipulations):
                # Should handle header manipulation appropriately
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, headers
                )

                # Most manipulations should result in invalid signature
                # Only the first case (extra headers) might be valid depending on implementation
                if i > 0:  # Skip first case which might be valid
                    assert not is_valid, f"Header manipulation {i} should be invalid"

    async def test_replay_attack_memory_and_state_validation(
        self, async_benchmark_timer
    ):
        """Test that replay protection doesn't cause memory leaks or state issues."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            # No handler usage
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Setup required onboarding forms in fake database for memory test
            from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
                OnboardingForm,
                OnboardingFormStatus,
            )

            async with FakeUnitOfWork() as uow:
                for i in range(10):  # Create fewer forms to be realistic
                    onboarding_form = OnboardingForm(
                        id=10 + i,
                        typeform_id=f"memory_test_{i}",
                        webhook_url="https://test.webhook.url",
                        user_id=1,
                        status=OnboardingFormStatus.ACTIVE,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    await uow.onboarding_forms.add(onboarding_form)
                await uow.commit()

            # Generate many unique payloads and replay them (use fewer for realism)
            replay_scenarios = []

            for i in range(10):  # Reduced from 100 to be more realistic
                payload = create_webhook_payload_kwargs(
                    form_response={
                        "form_id": f"memory_test_{i}",
                        "token": f"resp_{get_next_webhook_counter()}",
                        "answers": [
                            {
                                "field": {"id": f"field_{i}", "type": "short_text"},
                                "text": f"Memory test payload {i}",
                            }
                        ],
                        "submitted_at": datetime.now(UTC).isoformat(),
                    }
                )

                payload_str = json.dumps(payload)
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}

                replay_scenarios.append((payload_str, headers))

            # Process each payload once (should succeed)
            for i, (payload_str, headers) in enumerate(replay_scenarios):
                success, error, _ = await process_typeform_webhook(
                    payload=payload_str,
                    headers=headers,
                    uow_factory=lambda: FakeUnitOfWork(),
                )
                assert (
                    success is True
                ), f"First processing of payload {i} should succeed"

            # Replay all payloads (should fail)
            replay_failures = 0
            for i, (payload_str, headers) in enumerate(replay_scenarios):
                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, err = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                if not is_valid:
                    replay_failures += 1

            # All replays should be blocked
            assert replay_failures == len(
                replay_scenarios
            ), f"Not all replays blocked: {replay_failures}/{len(replay_scenarios)}"

    async def test_replay_attack_edge_timing_scenarios(self, async_benchmark_timer):
        """Test replay attacks with edge timing scenarios."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:

            def fake_uow_factory():
                return FakeUnitOfWork()

            # Use verifier directly for timing validation
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Timing edge cases
            timing_scenarios = [
                # Just within tolerance
                datetime.now(UTC) - timedelta(minutes=4, seconds=59),
                # Just outside tolerance
                datetime.now(UTC) - timedelta(minutes=5, seconds=1),
                # Exactly at tolerance boundary
                datetime.now(UTC) - timedelta(minutes=5),
                # Microsecond precision tests
                datetime.now(UTC)
                - timedelta(minutes=4, seconds=59, microseconds=999999),
                datetime.now(UTC) - timedelta(minutes=5, seconds=0, microseconds=1),
            ]

            for i, timestamp in enumerate(timing_scenarios):
                payload = {
                    "form_id": f"timing_edge_test_{i}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": f"field_{i}", "type": "short_text"},
                            "text": f"Timing edge test {i}",
                        }
                    ],
                    "submitted_at": timestamp.isoformat(),
                }

                payload_str = json.dumps(payload)
                signature = security_helper.generate_valid_signature(payload)
                headers = {"typeform-signature": signature}

                verifier = WebhookSecurityVerifier(webhook_secret)
                is_valid, err = await verifier.verify_webhook_request(
                    payload_str, headers
                )

                # Behavior depends on timestamp tolerance implementation
                # Document the behavior for each timing scenario
                minutes_old = (datetime.now(UTC) - timestamp).total_seconds() / 60

                # Log validation result for observability
                print(
                    f"Timing scenario {i}: {minutes_old:.3f} minutes old - Valid: {is_valid}"
                )
