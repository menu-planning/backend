"""
Signature Verification Stress Testing

Tests HMAC signature verification under high load conditions, edge cases,
and stress scenarios to ensure the security system remains robust under
production-level traffic and malicious attack patterns.

Validates performance, memory usage, and security under concurrent load.
"""

import asyncio
import gc
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timezone
from typing import Dict

import psutil
import pytest
from src.contexts.client_onboarding.core.services.exceptions import WebhookPayloadError
from src.contexts.client_onboarding.core.services.webhooks.security import (
    WebhookSecurityVerifier,
)
from tests.contexts.client_onboarding.fakes.webhook_security import (
    WebhookSecurityHelper,
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


class TestSignatureVerificationStress:
    """Stress testing for signature verification under high load."""

    async def test_concurrent_signature_verification_load(self, async_benchmark_timer):
        """Test signature verification under high concurrent load."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Generate test payloads
            test_payloads = []
            for i in range(100):
                payload = {
                    "form_id": f"stress_test_{i}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": f"field_{i}", "type": "short_text"},
                            "text": f"Stress test response {i}",
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(payload, separators=(",", ":"))
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}

                test_payloads.append((payload_str, headers))

            # Concurrent verification test
            async def verify_payload(payload_str: str, headers: dict[str, str]) -> bool:
                """Single verification task."""
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                return is_valid

            # Launch concurrent verifications
            start_time = time.perf_counter()
            tasks = [
                verify_payload(payload_str, headers)
                for payload_str, headers in test_payloads
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            # Verify all passed
            assert all(results), "All valid signatures should verify successfully"

            # Performance metrics
            total_time = end_time - start_time
            verifications_per_second = len(test_payloads) / total_time

            # Should handle at least 50 verifications per second
            assert (
                verifications_per_second > 50
            ), f"Performance too low: {verifications_per_second} req/s"

            print(
                f"Concurrent verification performance: {verifications_per_second:.2f} verifications/sec"
            )

    async def test_signature_verification_under_memory_pressure(
        self, async_benchmark_timer
    ):
        """Test signature verification behavior under memory pressure."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Monitor memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create large payload scenarios
            large_payloads = []
            for i in range(50):
                # Create progressively larger payloads
                large_text = "x" * (1000 * (i + 1))  # 1KB to 50KB
                payload = {
                    "form_id": f"memory_test_{i}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": f"field_{i}", "type": "long_text"},
                            "text": large_text,
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(payload, separators=(",", ":"))
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}

                large_payloads.append((payload_str, headers))

            # Process all large payloads
            verification_results = []
            for payload_str, headers in large_payloads:
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                verification_results.append(is_valid)

                # Force garbage collection periodically
                if len(verification_results) % 10 == 0:
                    gc.collect()

            # Check memory usage after processing
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory

            # All verifications should succeed
            assert all(
                verification_results
            ), "All large payload signatures should verify"

            # Memory growth should be reasonable (less than 100MB)
            assert (
                memory_growth < 100
            ), f"Excessive memory growth: {memory_growth:.2f}MB"

            print(
                f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (growth: {memory_growth:.2f}MB)"
            )

    async def test_rapid_sequential_verification_stress(self, async_benchmark_timer):
        """Test rapid sequential signature verifications without concurrency."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Generate many small payloads for rapid verification
            num_verifications = 1000
            payload_template = {
                "form_id": "rapid_test",
                "response_id": "resp_template",
                "answers": [
                    {
                        "field": {"id": "field_1", "type": "short_text"},
                        "text": "template_response",
                    }
                ],
                "submitted_at": datetime.now(UTC).isoformat(),
            }

            # Rapid sequential verification
            start_time = time.perf_counter()
            verification_times = []

            for i in range(num_verifications):
                # Modify payload slightly for each verification
                payload = payload_template.copy()
                payload["response_id"] = f"resp_{get_next_webhook_counter()}"

                payload_str = json.dumps(payload, separators=(",", ":"))
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}

                # Time individual verification
                verify_start = time.perf_counter()
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                verify_end = time.perf_counter()

                verification_times.append(verify_end - verify_start)
                assert is_valid, f"Verification {i} failed"

            end_time = time.perf_counter()

            # Performance analysis
            total_time = end_time - start_time
            avg_verification_time = sum(verification_times) / len(verification_times)
            max_verification_time = max(verification_times)
            verifications_per_second = num_verifications / total_time

            # Performance requirements
            assert (
                avg_verification_time < 0.01
            ), f"Average verification too slow: {avg_verification_time:.4f}s"
            assert (
                max_verification_time < 0.1
            ), f"Max verification too slow: {max_verification_time:.4f}s"
            assert (
                verifications_per_second > 100
            ), f"Throughput too low: {verifications_per_second:.2f} req/s"

            print(
                f"Rapid verification: {verifications_per_second:.2f} req/s, avg: {avg_verification_time*1000:.2f}ms, max: {max_verification_time*1000:.2f}ms"
            )

    async def test_signature_verification_with_malformed_edge_cases(
        self, async_benchmark_timer
    ):
        """Test signature verification with edge case malformed signatures."""

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

            # Edge case malformed signatures that might cause performance issues
            malformed_signatures = [
                # Very long signatures
                "sha256=" + "a" * 10000,
                "sha256=" + "b" * 100000,
                # Special characters that might cause issues
                "sha256=" + "".join(chr(i) for i in range(32, 127)) * 100,
                # Binary data (base64 encoded)
                "sha256=" + "".join(chr(i) for i in range(256)) * 10,
                # Repeated patterns that might trigger worst-case comparison
                "sha256=" + "abcd" * 10000,
                "sha256=" + "0123456789abcdef" * 1000,
                # Unicode edge cases
                "sha256=" + "café" * 1000,
                "sha256=" + "🔒" * 500,
                # Empty and null-like
                "",
                "sha256=",
                "sha256=" + "\x00" * 100,
            ]

            verification_times = []

            for malformed_sig in malformed_signatures:
                headers = {"typeform-signature": malformed_sig}

                # Measure verification time for malformed signature
                start_time = time.perf_counter()
                is_valid, error_msg = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                end_time = time.perf_counter()

                verification_time = end_time - start_time
                verification_times.append(verification_time)

                # Should be invalid and complete quickly
                assert (
                    not is_valid
                ), f"Malformed signature unexpectedly valid: {malformed_sig[:50]}..."
                assert (
                    verification_time < 1.0
                ), f"Verification too slow for malformed sig: {verification_time:.4f}s"

            # All malformed signatures should complete quickly
            max_verification_time = max(verification_times)
            avg_verification_time = sum(verification_times) / len(verification_times)

            assert (
                max_verification_time < 0.5
            ), f"Max malformed verification too slow: {max_verification_time:.4f}s"
            assert (
                avg_verification_time < 0.1
            ), f"Avg malformed verification too slow: {avg_verification_time:.4f}s"

            print(
                f"Malformed signature handling: avg {avg_verification_time*1000:.2f}ms, max {max_verification_time*1000:.2f}ms"
            )

    async def test_signature_verification_timing_consistency(
        self, async_benchmark_timer
    ):
        """Test timing consistency to prevent timing attack vulnerabilities."""

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

            # Generate correct signature
            correct_signature = security_helper.generate_valid_signature(test_payload)

            # Create signatures with varying degrees of correctness
            test_scenarios = [
                ("completely_wrong", "sha256=" + "a" * 64),
                (
                    "half_correct",
                    correct_signature[:30] + "a" * (len(correct_signature) - 30),
                ),
                ("almost_correct", correct_signature[:-2] + "aa"),
                ("one_char_wrong", correct_signature[:-1] + "a"),
                ("correct_signature", correct_signature),
            ]

            # Measure timing for each scenario multiple times
            timing_results = {}

            for scenario_name, signature in test_scenarios:
                times = []

                # Run each scenario multiple times with unique payloads to avoid replay detection
                for iteration in range(50):
                    # Create unique payload for each iteration to avoid replay protection
                    iteration_payload = {
                        "event_id": f"timing_test_{iteration}",
                        "event_type": "form_response",
                        "form_response": {
                            "form_id": "timing_test_form",
                            "response_id": f"resp_{iteration}",
                            "answers": [],
                        },
                    }
                    iteration_payload_str = json.dumps(
                        iteration_payload, separators=(",", ":")
                    )

                    # Use the same signature pattern but for the unique payload if it's the correct scenario
                    if scenario_name == "correct_signature":
                        iteration_signature = security_helper.generate_valid_signature(
                            iteration_payload_str
                        )
                    else:
                        iteration_signature = (
                            signature  # Use the incorrect signature as-is
                        )

                    headers = {"typeform-signature": iteration_signature}

                    start_time = time.perf_counter()
                    is_valid, _ = await verifier.verify_webhook_request(
                        iteration_payload_str, headers
                    )
                    end_time = time.perf_counter()

                    times.append(end_time - start_time)

                    # Only correct signature should be valid
                    expected_valid = scenario_name == "correct_signature"
                    assert (
                        is_valid == expected_valid
                    ), f"Unexpected validation result for {scenario_name}"

                timing_results[scenario_name] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "times": times,
                }

            # Analyze timing consistency
            # All invalid signature timings should be similar (within reasonable variance)
            invalid_scenarios = [
                name for name in timing_results if name != "correct_signature"
            ]
            invalid_avg_times = [
                timing_results[name]["avg"] for name in invalid_scenarios
            ]

            # Calculate timing variance for invalid signatures
            min_invalid_time = min(invalid_avg_times)
            max_invalid_time = max(invalid_avg_times)
            timing_variance = max_invalid_time - min_invalid_time

            # Timing variance should be minimal to prevent timing attacks
            assert (
                timing_variance < 0.05
            ), f"Timing variance too high: {timing_variance:.6f}s"

            # All timings should be reasonably fast
            for scenario_name, results in timing_results.items():
                assert (
                    results["max"] < 0.1
                ), f"{scenario_name} max time too slow: {results['max']:.6f}s"

            print(
                f"Timing consistency verified - variance: {timing_variance*1000:.2f}ms"
            )

    async def test_memory_leak_detection_during_stress(self, async_benchmark_timer):
        """Test for memory leaks during extended signature verification stress."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Monitor memory over time
            process = psutil.Process(os.getpid())
            memory_samples = []

            # Baseline memory
            gc.collect()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(baseline_memory)

            # Run verification cycles
            cycles = 10
            verifications_per_cycle = 100

            for cycle in range(cycles):
                # Generate payloads for this cycle
                for i in range(verifications_per_cycle):
                    payload = {
                        "form_id": f"leak_test_{cycle}_{i}",
                        "response_id": f"resp_{get_next_webhook_counter()}",
                        "answers": [
                            {
                                "field": {"id": f"field_{i}", "type": "short_text"},
                                "text": f"Leak test cycle {cycle} iteration {i}",
                            }
                        ],
                        "submitted_at": datetime.now(UTC).isoformat(),
                    }

                    payload_str = json.dumps(payload, separators=(",", ":"))
                    signature = security_helper.generate_valid_signature(payload_str)
                    headers = {"typeform-signature": signature}

                    # Verify signature
                    is_valid, _ = await verifier.verify_webhook_request(
                        payload_str, headers
                    )
                    assert (
                        is_valid
                    ), f"Verification failed at cycle {cycle}, iteration {i}"

                # Sample memory after each cycle
                gc.collect()  # Force garbage collection
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)

                print(f"Cycle {cycle + 1}/{cycles}: {current_memory:.2f}MB")

            # Analyze memory growth
            final_memory = memory_samples[-1]
            memory_growth = final_memory - baseline_memory

            # Calculate memory growth trend
            if len(memory_samples) > 2:
                # Simple linear regression to detect consistent growth
                x = list(range(len(memory_samples)))
                y = memory_samples
                n = len(x)

                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i] * y[i] for i in range(n))
                sum_x2 = sum(x[i] ** 2 for i in range(n))

                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

                # Slope should be minimal (no significant growth trend)
                assert (
                    abs(slope) < 0.5
                ), f"Potential memory leak detected - growth rate: {slope:.3f}MB/cycle"

            # Total memory growth should be reasonable
            assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.2f}MB"

            print(
                f"Memory leak test passed - growth: {memory_growth:.2f}MB over {cycles} cycles"
            )

    async def test_concurrent_mixed_valid_invalid_signatures(
        self, async_benchmark_timer
    ):
        """Test concurrent verification of mixed valid and invalid signatures."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Generate mixed valid and invalid signature scenarios
            verification_tasks = []
            expected_results = []

            for i in range(200):  # 200 concurrent verifications
                payload = {
                    "form_id": f"mixed_test_{i}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": f"field_{i}", "type": "short_text"},
                            "text": f"Mixed test response {i}",
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(payload, separators=(",", ":"))

                # Alternate between valid and invalid signatures
                if i % 2 == 0:
                    # Valid signature
                    signature = security_helper.generate_valid_signature(payload_str)
                    expected_results.append(True)
                else:
                    # Invalid signature
                    signature = f"sha256={'invalid_' + str(i):0<64}"
                    expected_results.append(False)

                headers = {"typeform-signature": signature}
                verification_tasks.append((payload_str, headers))

            # Concurrent verification function
            async def verify_signature(
                payload_str: str, headers: dict[str, str]
            ) -> bool:
                """Verify a single signature."""
                is_valid, _ = await verifier.verify_webhook_request(
                    payload_str, headers
                )
                return is_valid

            # Launch all verifications concurrently
            start_time = time.perf_counter()
            tasks = [
                verify_signature(payload_str, headers)
                for payload_str, headers in verification_tasks
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            # Verify results match expectations
            assert len(results) == len(expected_results)
            for i, (actual, expected) in enumerate(
                zip(results, expected_results, strict=False)
            ):
                assert (
                    actual == expected
                ), f"Verification {i} mismatch: expected {expected}, got {actual}"

            # Performance metrics
            total_time = end_time - start_time
            verifications_per_second = len(verification_tasks) / total_time

            # Should handle mixed load efficiently
            assert (
                verifications_per_second > 30
            ), f"Mixed verification performance too low: {verifications_per_second:.2f} req/s"

            # Count valid vs invalid
            valid_count = sum(expected_results)
            invalid_count = len(expected_results) - valid_count

            print(
                f"Mixed verification: {verifications_per_second:.2f} req/s ({valid_count} valid, {invalid_count} invalid)"
            )


class TestSignatureVerificationEdgeCases:
    """Edge case testing for signature verification."""

    async def test_extreme_payload_sizes(self, async_benchmark_timer):
        """Test signature verification with extreme payload sizes."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Test various payload sizes
            size_tests = [
                ("tiny", 10),  # 10 bytes
                ("small", 1000),  # 1KB
                ("medium", 10000),  # 10KB
                ("large", 100000),  # 100KB
                ("very_large", 500000),  # 500KB
            ]

            for size_name, content_size in size_tests:
                # Create payload with specific content size
                large_content = "x" * content_size
                payload = {
                    "form_id": f"size_test_{size_name}",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "long_text"},
                            "text": large_content,
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(payload, separators=(",", ":"))
                actual_size = len(payload_str.encode("utf-8"))

                # Test verification timing
                start_time = time.perf_counter()

                if actual_size > verifier.max_payload_size:
                    # Should reject large payloads quickly
                    with pytest.raises(WebhookPayloadError):
                        signature = security_helper.generate_valid_signature(
                            payload_str
                        )
                        headers = {"typeform-signature": signature}
                        await verifier.verify_webhook_request(payload_str, headers)
                else:
                    # Should verify successfully within time limits
                    signature = security_helper.generate_valid_signature(payload_str)
                    headers = {"typeform-signature": signature}
                    is_valid, _ = await verifier.verify_webhook_request(
                        payload_str, headers
                    )
                    assert is_valid, f"Valid signature failed for {size_name} payload"

                verification_time = time.perf_counter() - start_time

                # Should complete within reasonable time regardless of size
                max_time = 0.1 if actual_size <= verifier.max_payload_size else 0.05
                assert (
                    verification_time < max_time
                ), f"{size_name} verification too slow: {verification_time:.4f}s"

                print(
                    f"{size_name} payload ({actual_size} bytes): {verification_time*1000:.2f}ms"
                )

    async def test_signature_verification_error_handling(self, async_benchmark_timer):
        """Test error handling during signature verification stress."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)

            # Error scenarios that should be handled gracefully
            error_scenarios = [
                # Missing signature header
                (
                    "missing_signature",
                    {},
                    '{"event_id": "test_123", "event_type": "form_response"}',
                ),
                # Empty payload
                ("empty_payload", {"typeform-signature": "sha256=test"}, ""),
                # Invalid JSON payload
                (
                    "invalid_json",
                    {"typeform-signature": "sha256=test"},
                    "{invalid json",
                ),
                # None values
                ("none_payload", {"typeform-signature": "sha256=test"}, None),
                # Binary payload
                (
                    "binary_payload",
                    {"typeform-signature": "sha256=test"},
                    b"binary data",
                ),
            ]

            for scenario_name, headers, payload in error_scenarios:
                start_time = time.perf_counter()

                try:
                    if payload is None:
                        # Skip None payload as it would cause TypeError before reaching verifier
                        continue

                    if isinstance(payload, bytes):
                        # Convert bytes to string for testing
                        payload = payload.decode("utf-8", errors="ignore")

                    is_valid, error_msg = await verifier.verify_webhook_request(
                        payload, headers
                    )

                    # Should be invalid with descriptive error
                    assert (
                        not is_valid
                    ), f"Error scenario {scenario_name} unexpectedly valid"
                    assert (
                        error_msg is not None
                    ), f"Error scenario {scenario_name} missing error message"

                except (ValueError, TypeError, json.JSONDecodeError):
                    # Acceptable exceptions for malformed input
                    pass

                verification_time = time.perf_counter() - start_time

                # Error handling should be fast
                assert (
                    verification_time < 0.1
                ), f"Error handling too slow for {scenario_name}: {verification_time:.4f}s"

                print(
                    f"Error scenario '{scenario_name}': {verification_time*1000:.2f}ms"
                )

    async def test_signature_verification_under_cpu_stress(self, async_benchmark_timer):
        """Test signature verification performance under CPU stress."""

        # Use the validated environment secret
        webhook_secret = WEBHOOK_SECRET

        async with async_benchmark_timer() as timer:
            verifier = WebhookSecurityVerifier(webhook_secret)
            security_helper = WebhookSecurityHelper(webhook_secret)

            # Create CPU stress in background
            def cpu_stress_worker():
                """CPU-intensive background task."""
                end_time = time.time() + 5  # Run for 5 seconds
                while time.time() < end_time:
                    # CPU-intensive calculation
                    sum(i * i for i in range(10000))

            # Start CPU stress in background threads
            cpu_cores = os.cpu_count() or 4
            with ThreadPoolExecutor(max_workers=cpu_cores) as executor:
                # Launch CPU stress tasks
                stress_futures = [
                    executor.submit(cpu_stress_worker) for _ in range(cpu_cores)
                ]

                # Perform signature verification under CPU stress
                payload = {
                    "form_id": "cpu_stress_test",
                    "response_id": f"resp_{get_next_webhook_counter()}",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "short_text"},
                            "text": "CPU stress test response",
                        }
                    ],
                    "submitted_at": datetime.now(UTC).isoformat(),
                }

                payload_str = json.dumps(payload, separators=(",", ":"))
                signature = security_helper.generate_valid_signature(payload_str)
                headers = {"typeform-signature": signature}

                # Perform multiple verifications under stress
                verification_times = []
                num_verifications = 50

                for i in range(num_verifications):
                    # Create unique payload for each verification to avoid replay detection
                    unique_payload = {
                        "event_id": f"cpu_stress_test_{i}",
                        "event_type": "form_response",
                        "form_response": {
                            "form_id": "cpu_stress_test_form",
                            "response_id": f"resp_stress_{i}",
                            "answers": [
                                {
                                    "field": {"id": "field_1", "type": "short_text"},
                                    "text": f"CPU stress test response {i}",
                                }
                            ],
                            "submitted_at": datetime.now(UTC).isoformat(),
                        },
                    }

                    unique_payload_str = json.dumps(
                        unique_payload, separators=(",", ":")
                    )
                    unique_signature = security_helper.generate_valid_signature(
                        unique_payload_str
                    )
                    unique_headers = {"typeform-signature": unique_signature}

                    start_time = time.perf_counter()
                    is_valid, _ = await verifier.verify_webhook_request(
                        unique_payload_str, unique_headers
                    )
                    end_time = time.perf_counter()

                    assert is_valid, f"Verification {i} failed under CPU stress"
                    verification_times.append(end_time - start_time)

                # Wait for CPU stress to complete
                for future in as_completed(stress_futures, timeout=10):
                    pass

            # Analyze performance under stress
            avg_time = sum(verification_times) / len(verification_times)
            max_time = max(verification_times)

            # Performance should remain reasonable even under CPU stress
            assert (
                avg_time < 0.1
            ), f"Average verification time too slow under CPU stress: {avg_time:.4f}s"
            assert (
                max_time < 0.5
            ), f"Max verification time too slow under CPU stress: {max_time:.4f}s"

            print(
                f"CPU stress test: avg {avg_time*1000:.2f}ms, max {max_time*1000:.2f}ms"
            )
