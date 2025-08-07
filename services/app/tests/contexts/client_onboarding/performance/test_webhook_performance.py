"""
Performance tests for overall webhook processing under realistic load.

Tests webhook reception, signature verification, database storage, and response
generation performance to validate production readiness under typical usage patterns.
"""

import pytest
import asyncio
import time
import json
import statistics
import gc
from datetime import datetime, UTC
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List, Optional
import hashlib
import hmac
import base64

from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.services.webhook_security import WebhookSecurityVerifier
from src.contexts.client_onboarding.core.domain.models import OnboardingForm, FormResponse
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.contexts.client_onboarding.data_factories import (
    create_typeform_webhook_payload,
    create_onboarding_form
)
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)

pytestmark = pytest.mark.anyio


class PerformanceWebhookGenerator:
    """High-performance webhook payload generator for load testing."""
    
    def __init__(self, webhook_secret: str = "test_webhook_secret"):
        self.webhook_secret = webhook_secret
        self.payload_count = 0
        
    def generate_webhook_payload(
        self, 
        form_id: Optional[str] = None,
        include_signature: bool = True,
        field_count: int = 5
    ) -> Dict[str, Any]:
        """Generate realistic webhook payload with configurable complexity."""
        if not form_id:
            form_id = f"form_{get_next_onboarding_form_id()}"
        
        self.payload_count += 1
        
        # Generate realistic form submission data
        field_responses = []
        for i in range(field_count):
            field_responses.append({
                "field": {
                    "id": f"field_{i}_{self.payload_count}",
                    "type": "short_text" if i % 2 == 0 else "email",
                    "ref": f"field_ref_{i}"
                },
                "type": "text" if i % 2 == 0 else "email",
                "text": f"Response value {i} for payload {self.payload_count}" if i % 2 == 0 else f"user{i}@example.com"
            })
        
        # Create webhook payload
        payload_data = {
            "event_id": f"perf_event_{self.payload_count}_{get_next_webhook_counter()}",
            "event_type": "form_response",
            "form_response": {
                "form_id": form_id,
                "token": f"perf_token_{self.payload_count}",
                "submitted_at": datetime.now(UTC).isoformat(),
                "definition": {
                    "id": form_id,
                    "title": f"Performance Test Form {self.payload_count}",
                    "fields": [resp["field"] for resp in field_responses]
                },
                "answers": field_responses
            }
        }
        
        result = {"payload": json.dumps(payload_data)}
        
        if include_signature:
            result["signature"] = self._generate_signature(result["payload"])
            
        return result
    
    def _generate_signature(self, payload: str) -> str:
        """Generate TypeForm-compliant HMAC-SHA256 signature."""
        # TypeForm algorithm: payload + newline -> HMAC-SHA256 -> base64 -> sha256= prefix
        payload_with_newline = payload + "\n"
        signature_bytes = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_with_newline.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        return f"sha256={signature_b64}"


class TestWebhookProcessingPerformance:
    """Performance tests for complete webhook processing pipeline."""
    
    def setup_method(self):
        """Set up performance test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.webhook_secret = "performance_test_secret_key"
        self.payload_generator = PerformanceWebhookGenerator(self.webhook_secret)
        self.fake_uow = FakeUnitOfWork()
        
        # Create webhook handler with performance-optimized settings
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
    
    async def test_single_webhook_processing_latency(self):
        """Test latency for processing a single webhook request."""
        # Generate test payload
        webhook_data = self.payload_generator.generate_webhook_payload()
        
        # Setup test form in repository
        form_id = json.loads(webhook_data["payload"])["form_response"]["form_id"]
        test_form = create_onboarding_form(
            typeform_id=form_id,
            webhook_url="https://test.example.com/webhook",
            name="Performance Test Form"
        )
        await self.fake_uow.onboarding_forms.add(test_form)
        
        # Measure processing latency
        start_time = time.perf_counter()
        
        # Process webhook
        headers = {"Typeform-Signature": webhook_data["signature"]}
        status_code, result = await self.webhook_handler.handle_webhook(
            payload=webhook_data["payload"],
            headers=headers,
            webhook_secret=self.webhook_secret
        )
        
        end_time = time.perf_counter()
        processing_latency_ms = (end_time - start_time) * 1000
        
        # Latency assertions
        assert status_code == 200, f"Expected status 200, got {status_code}"
        assert result.get("status") == "success", f"Expected success, got {result}"
        
        # Single webhook processing should be very fast (< 50ms)
        assert processing_latency_ms < 50.0, f"Processing latency {processing_latency_ms:.2f}ms, expected < 50ms"
        
        # Verify data was stored correctly
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert isinstance(stored_responses, list)
        assert len(stored_responses) == 1
        
        print(f"✅ Single webhook processing latency: {processing_latency_ms:.2f}ms")
    
    async def test_concurrent_webhook_processing_performance(self):
        """Test performance under concurrent webhook processing load."""
        concurrent_requests = 50
        webhooks_per_request = 10
        total_webhooks = concurrent_requests * webhooks_per_request
        
        # Setup test forms
        form_ids = []
        for i in range(5):  # Use 5 different forms for variety
            form_id = f"concurrent_form_{i}_{get_next_onboarding_form_id()}"
            form_ids.append(form_id)
            
            test_form = create_onboarding_form(
                typeform_id=form_id,
                webhook_url=f"https://test.example.com/webhook/{i}",
                name=f"Concurrent Test Form {i}"
            )
            await self.fake_uow.onboarding_forms.add(test_form)
        
        async def process_webhook_batch(batch_id: int):
            """Process a batch of webhooks concurrently."""
            batch_results = []
            batch_start = time.perf_counter()
            
            for i in range(webhooks_per_request):
                # Use different forms for variety
                form_id = form_ids[i % len(form_ids)]
                webhook_data = self.payload_generator.generate_webhook_payload(form_id=form_id)
                
                headers = {"Typeform-Signature": webhook_data["signature"]}
                
                try:
                    status_code, result = await self.webhook_handler.handle_webhook(
                        payload=webhook_data["payload"],
                        headers=headers,
                        webhook_secret=self.webhook_secret
                    )
                    batch_results.append({"success": status_code == 200, "result": result})
                except Exception as e:
                    batch_results.append({"success": False, "error": str(e)})
            
            batch_duration = time.perf_counter() - batch_start
            return {
                "batch_id": batch_id,
                "results": batch_results,
                "duration": batch_duration,
                "webhooks_processed": len(batch_results)
            }
        
        # Execute concurrent batches
        start_time = time.perf_counter()
        
        tasks = [process_webhook_batch(i) for i in range(concurrent_requests)]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_batches = [r for r in batch_results if isinstance(r, dict) and not isinstance(r, Exception)]
        total_processed = sum(batch["webhooks_processed"] for batch in successful_batches)
        successful_webhooks = sum(
            sum(1 for result in batch["results"] if result.get("success", False))
            for batch in successful_batches
        )
        
        # Performance assertions
        assert len(successful_batches) == concurrent_requests, f"Only {len(successful_batches)}/{concurrent_requests} batches successful"
        assert total_processed == total_webhooks, f"Processed {total_processed}/{total_webhooks} webhooks"
        
        # Success rate should be high (> 95%)
        success_rate = (successful_webhooks / total_processed) * 100
        assert success_rate > 95.0, f"Success rate {success_rate:.1f}%, expected > 95%"
        
        # Processing rate should be efficient
        processing_rate = total_processed / total_duration
        assert processing_rate > 100, f"Processing rate {processing_rate:.1f}/s, expected > 100/s"
        
        # Concurrent processing should complete reasonably quickly
        assert total_duration < 30.0, f"Total duration {total_duration:.2f}s, expected < 30s"
        
        # Verify data integrity
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert isinstance(stored_responses, list)
        assert len(stored_responses) == successful_webhooks
        
        print(f"✅ Concurrent processing performance:")
        print(f"   {total_processed} webhooks in {total_duration:.2f}s ({processing_rate:.1f}/s)")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Concurrency: {concurrent_requests} batches")
    
    async def test_signature_verification_performance_under_load(self):
        """Test HMAC signature verification performance under high load."""
        verification_count = 1000
        payloads = []
        
        # Pre-generate payloads for consistent testing
        for i in range(verification_count):
            webhook_data = self.payload_generator.generate_webhook_payload(
                field_count=10  # Larger payloads for more realistic testing
            )
            payloads.append(webhook_data)
        
        # Test signature verification performance
        verifier = WebhookSecurityVerifier(self.webhook_secret)
        start_time = time.perf_counter()
        
        verification_results = []
        for webhook_data in payloads:
            # Verify signature using security verifier
            try:
                headers = {"Typeform-Signature": webhook_data["signature"]}
                is_valid, error_msg = await verifier.verify_webhook_request(
                    webhook_data["payload"],
                    headers
                )
                verification_results.append(is_valid)
            except Exception as e:
                verification_results.append(False)
        
        end_time = time.perf_counter()
        verification_duration = end_time - start_time
        
        # Performance assertions
        successful_verifications = sum(verification_results)
        verification_rate = verification_count / verification_duration
        avg_verification_time_ms = (verification_duration / verification_count) * 1000
        
        # All signatures should verify successfully
        assert successful_verifications == verification_count, f"Only {successful_verifications}/{verification_count} signatures verified"
        
        # Signature verification should be fast
        assert verification_rate > 500, f"Verification rate {verification_rate:.1f}/s, expected > 500/s"
        assert avg_verification_time_ms < 2.0, f"Average verification time {avg_verification_time_ms:.2f}ms, expected < 2ms"
        
        print(f"✅ Signature verification performance:")
        print(f"   {verification_count} verifications in {verification_duration:.3f}s ({verification_rate:.1f}/s)")
        print(f"   Average verification time: {avg_verification_time_ms:.2f}ms")
    
    async def test_database_storage_performance_under_load(self):
        """Test database storage performance for form responses under load."""
        storage_count = 500
        
        # Setup test form
        form_id = f"storage_perf_form_{get_next_onboarding_form_id()}"
        test_form = create_onboarding_form(
            typeform_id=form_id,
            webhook_url="https://test.example.com/webhook",
            name="Storage Performance Test Form"
        )
        await self.fake_uow.onboarding_forms.add(test_form)
        
        # Generate webhook payloads
        webhook_payloads = []
        for i in range(storage_count):
            webhook_data = self.payload_generator.generate_webhook_payload(
                form_id=form_id,
                field_count=8  # Moderate complexity
            )
            webhook_payloads.append(webhook_data)
        
        # Measure storage performance
        start_time = time.perf_counter()
        
        storage_results = []
        for webhook_data in webhook_payloads:
            headers = {"Typeform-Signature": webhook_data["signature"]}
            
            try:
                status_code, result = await self.webhook_handler.handle_webhook(
                    payload=webhook_data["payload"],
                    headers=headers,
                    webhook_secret=self.webhook_secret
                )
                storage_results.append(status_code == 200)
            except Exception:
                storage_results.append(False)
        
        end_time = time.perf_counter()
        storage_duration = end_time - start_time
        
        # Performance assertions
        successful_storage = sum(storage_results)
        storage_rate = storage_count / storage_duration
        avg_storage_time_ms = (storage_duration / storage_count) * 1000
        
        # All webhooks should be stored successfully
        assert successful_storage == storage_count, f"Only {successful_storage}/{storage_count} webhooks stored"
        
        # Storage should be efficient
        assert storage_rate > 50, f"Storage rate {storage_rate:.1f}/s, expected > 50/s"
        assert avg_storage_time_ms < 20.0, f"Average storage time {avg_storage_time_ms:.2f}ms, expected < 20ms"
        
        # Verify data integrity
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert isinstance(stored_responses, list)
        assert len(stored_responses) == storage_count
        
        print(f"✅ Database storage performance:")
        print(f"   {storage_count} responses stored in {storage_duration:.2f}s ({storage_rate:.1f}/s)")
        print(f"   Average storage time: {avg_storage_time_ms:.2f}ms")
    
    async def test_memory_usage_under_sustained_webhook_load(self):
        """Test memory usage remains stable under sustained webhook processing."""
        import psutil
        import os
        
        # Get baseline memory usage
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Setup test forms
        form_ids = []
        for i in range(3):
            form_id = f"memory_test_form_{i}_{get_next_onboarding_form_id()}"
            form_ids.append(form_id)
            
            test_form = create_onboarding_form(
                typeform_id=form_id,
                webhook_url=f"https://test.example.com/webhook/{i}",
                name=f"Memory Test Form {i}"
            )
            await self.fake_uow.onboarding_forms.add(test_form)
        
        # Sustained load test - multiple rounds
        rounds = 5
        webhooks_per_round = 100
        memory_samples = []
        
        for round_num in range(rounds):
            round_start = time.perf_counter()
            
            # Process webhooks for this round
            for i in range(webhooks_per_round):
                form_id = form_ids[i % len(form_ids)]
                webhook_data = self.payload_generator.generate_webhook_payload(form_id=form_id)
                
                headers = {"Typeform-Signature": webhook_data["signature"]}
                
                await self.webhook_handler.handle_webhook(
                    payload=webhook_data["payload"],
                    headers=headers,
                    webhook_secret=self.webhook_secret
                )
            
            round_duration = time.perf_counter() - round_start
            
            # Force garbage collection and measure memory
            gc.collect()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory_mb)
            
            print(f"   Round {round_num + 1}: {webhooks_per_round} webhooks in {round_duration:.2f}s, "
                  f"memory: {current_memory_mb:.1f}MB")
        
        final_memory_mb = memory_samples[-1]
        memory_growth_mb = final_memory_mb - initial_memory_mb
        
        # Memory assertions
        # Memory growth should be reasonable (< 100MB) under sustained load
        max_acceptable_growth_mb = 100
        assert memory_growth_mb < max_acceptable_growth_mb, f"Memory grew by {memory_growth_mb:.1f}MB, expected < {max_acceptable_growth_mb}MB"
        
        # Memory usage should be relatively stable
        if len(memory_samples) > 1:
            memory_variance = statistics.variance(memory_samples)
            assert memory_variance < 200, f"Memory variance {memory_variance:.1f}, expected stable usage"
        
        # Verify all data was processed
        total_webhooks = rounds * webhooks_per_round
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert isinstance(stored_responses, list)
        assert len(stored_responses) == total_webhooks
        
        print(f"✅ Memory usage under sustained load:")
        print(f"   {total_webhooks} webhooks processed across {rounds} rounds")
        print(f"   Memory: {initial_memory_mb:.1f}MB → {final_memory_mb:.1f}MB (+{memory_growth_mb:.1f}MB)")


class TestWebhookPerformanceStress:
    """Stress tests for webhook processing under extreme conditions."""
    
    def setup_method(self):
        """Set up stress test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.webhook_secret = "stress_test_secret_key"
        self.payload_generator = PerformanceWebhookGenerator(self.webhook_secret)
        self.fake_uow = FakeUnitOfWork()
        
        # Create webhook handler
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
    
    async def test_extreme_concurrent_webhook_processing(self):
        """Stress test with extreme concurrent webhook processing load."""
        concurrent_tasks = 100
        webhooks_per_task = 5
        total_webhooks = concurrent_tasks * webhooks_per_task
        
        # Setup test form
        form_id = f"stress_form_{get_next_onboarding_form_id()}"
        test_form = create_onboarding_form(
            typeform_id=form_id,
            webhook_url="https://test.example.com/webhook",
            name="Stress Test Form"
        )
        await self.fake_uow.onboarding_forms.add(test_form)
        
        async def stress_task(task_id: int):
            """Process webhooks under stress conditions."""
            task_results = []
            
            for i in range(webhooks_per_task):
                webhook_data = self.payload_generator.generate_webhook_payload(
                    form_id=form_id,
                    field_count=15  # Complex payloads for stress testing
                )
                
                headers = {"Typeform-Signature": webhook_data["signature"]}
                
                try:
                    status_code, result = await self.webhook_handler.handle_webhook(
                        payload=webhook_data["payload"],
                        headers=headers,
                        webhook_secret=self.webhook_secret
                    )
                    task_results.append(status_code == 200)
                except Exception:
                    task_results.append(False)
            
            return task_results
        
        # Execute stress test
        start_time = time.perf_counter()
        
        tasks = [stress_task(i) for i in range(concurrent_tasks)]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        stress_duration = end_time - start_time
        
        # Analyze stress test results
        successful_tasks = [r for r in task_results if isinstance(r, list)]
        total_processed = sum(len(task_result) for task_result in successful_tasks)
        successful_webhooks = sum(
            sum(task_result) for task_result in successful_tasks
        )
        
        # Stress test assertions
        assert len(successful_tasks) == concurrent_tasks, f"Only {len(successful_tasks)}/{concurrent_tasks} tasks completed"
        assert total_processed == total_webhooks, f"Processed {total_processed}/{total_webhooks} webhooks"
        
        # Success rate should remain high even under stress
        success_rate = (successful_webhooks / total_processed) * 100 if total_processed > 0 else 0
        assert success_rate > 90.0, f"Success rate {success_rate:.1f}% under stress, expected > 90%"
        
        # Should maintain reasonable performance under stress
        processing_rate = total_processed / stress_duration
        assert processing_rate > 50, f"Stress processing rate {processing_rate:.1f}/s, expected > 50/s"
        
        print(f"✅ Extreme concurrent stress test:")
        print(f"   {total_processed} webhooks with {concurrent_tasks} concurrent tasks")
        print(f"   Duration: {stress_duration:.2f}s ({processing_rate:.1f}/s)")
        print(f"   Success rate: {success_rate:.1f}%")
    
    async def test_large_payload_processing_performance(self):
        """Test performance with very large webhook payloads."""
        large_payload_count = 50
        fields_per_payload = 50  # Very large forms
        
        # Setup test form
        form_id = f"large_payload_form_{get_next_onboarding_form_id()}"
        test_form = create_onboarding_form(
            typeform_id=form_id,
            webhook_url="https://test.example.com/webhook",
            name="Large Payload Test Form"
        )
        await self.fake_uow.onboarding_forms.add(test_form)
        
        # Generate large payloads
        large_payloads = []
        for i in range(large_payload_count):
            webhook_data = self.payload_generator.generate_webhook_payload(
                form_id=form_id,
                field_count=fields_per_payload
            )
            large_payloads.append(webhook_data)
        
        # Measure large payload processing performance
        start_time = time.perf_counter()
        
        processing_results = []
        for webhook_data in large_payloads:
            headers = {"Typeform-Signature": webhook_data["signature"]}
            
            try:
                status_code, result = await self.webhook_handler.handle_webhook(
                    payload=webhook_data["payload"],
                    headers=headers,
                    webhook_secret=self.webhook_secret
                )
                processing_results.append(status_code == 200)
            except Exception:
                processing_results.append(False)
        
        end_time = time.perf_counter()
        large_payload_duration = end_time - start_time
        
        # Large payload performance assertions
        successful_processing = sum(processing_results)
        processing_rate = large_payload_count / large_payload_duration
        avg_processing_time_ms = (large_payload_duration / large_payload_count) * 1000
        
        # All large payloads should be processed successfully
        assert successful_processing == large_payload_count, f"Only {successful_processing}/{large_payload_count} large payloads processed"
        
        # Should maintain reasonable performance with large payloads
        assert processing_rate > 10, f"Large payload processing rate {processing_rate:.1f}/s, expected > 10/s"
        assert avg_processing_time_ms < 100, f"Average large payload processing time {avg_processing_time_ms:.1f}ms, expected < 100ms"
        
        print(f"✅ Large payload processing performance:")
        print(f"   {large_payload_count} payloads with {fields_per_payload} fields each")
        print(f"   Duration: {large_payload_duration:.2f}s ({processing_rate:.1f}/s)")
        print(f"   Average processing time: {avg_processing_time_ms:.1f}ms")