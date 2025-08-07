"""
Memory and resource usage performance tests.

Tests memory consumption, CPU usage, file descriptors, and other system resources
under realistic load to validate production readiness and resource efficiency.
"""

import pytest
import asyncio
import time
import gc
import os
import statistics
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, List, Optional
import threading
import concurrent.futures

from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.services.webhook_retry import (
    WebhookRetryManager, WebhookRetryPolicyConfig
)
from src.contexts.client_onboarding.core.services.typeform_client import TypeFormClient
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.contexts.client_onboarding.fakes.fake_typeform_api import (
    create_fake_httpx_client, FakeTypeFormAPI
)
from tests.contexts.client_onboarding.data_factories import (
    create_typeform_webhook_payload,
    create_onboarding_form
)
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    get_next_typeform_api_counter,
    reset_all_counters
)

pytestmark = pytest.mark.anyio

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def create_webhook_payload_with_signature(form_id: str, token: str, webhook_secret: str) -> tuple[str, Dict[str, str]]:
    """Create webhook payload and signature headers for testing."""
    import hmac
    import hashlib
    import base64
    import json
    
    # Generate webhook payload
    webhook_payload = create_typeform_webhook_payload(
        form_response={
            "form_id": form_id,
            "token": token
        }
    )
    payload_json = json.dumps(webhook_payload)
    
    # Create signature
    signature_data = payload_json + "\n"
    signature = hmac.new(
        webhook_secret.encode(),
        signature_data.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode()
    
    headers = {"Typeform-Signature": f"sha256={signature_b64}"}
    
    return payload_json, headers


class ResourceMonitor:
    """System resource monitoring utility for performance tests."""
    
    def __init__(self):
        self.process = None
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
        self.samples = []
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 0.1  # 100ms sampling rate
    
    def start_monitoring(self):
        """Start continuous resource monitoring."""
        if not PSUTIL_AVAILABLE:
            return
        
        self.monitoring = True
        self.samples.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring and return collected data."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        return self.get_resource_summary()
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            if PSUTIL_AVAILABLE and self.process:
                try:
                    memory_info = self.process.memory_info()
                    cpu_percent = self.process.cpu_percent()
                    num_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
                    num_threads = self.process.num_threads()
                    
                    sample = {
                        "timestamp": time.perf_counter(),
                        "memory_rss_mb": memory_info.rss / 1024 / 1024,
                        "memory_vms_mb": memory_info.vms / 1024 / 1024,
                        "cpu_percent": cpu_percent,
                        "num_file_descriptors": num_fds,
                        "num_threads": num_threads,
                        "gc_objects": len(gc.get_objects())
                    }
                    self.samples.append(sample)
                except Exception:
                    # Ignore monitoring errors
                    pass
            
            time.sleep(self.monitor_interval)
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage from samples."""
        if not self.samples:
            return {"error": "No samples collected"}
        
        # Calculate statistics for each metric
        memory_rss = [s["memory_rss_mb"] for s in self.samples]
        memory_vms = [s["memory_vms_mb"] for s in self.samples]
        cpu_percents = [s["cpu_percent"] for s in self.samples if s["cpu_percent"] > 0]
        file_descriptors = [s["num_file_descriptors"] for s in self.samples]
        threads = [s["num_threads"] for s in self.samples]
        gc_objects = [s["gc_objects"] for s in self.samples]
        
        return {
            "sample_count": len(self.samples),
            "duration_seconds": self.samples[-1]["timestamp"] - self.samples[0]["timestamp"],
            "memory_rss_mb": {
                "min": min(memory_rss),
                "max": max(memory_rss),
                "avg": statistics.mean(memory_rss),
                "growth": max(memory_rss) - min(memory_rss)
            },
            "memory_vms_mb": {
                "min": min(memory_vms),
                "max": max(memory_vms),
                "avg": statistics.mean(memory_vms),
                "growth": max(memory_vms) - min(memory_vms)
            },
            "cpu_percent": {
                "max": max(cpu_percents) if cpu_percents else 0,
                "avg": statistics.mean(cpu_percents) if cpu_percents else 0
            },
            "file_descriptors": {
                "min": min(file_descriptors),
                "max": max(file_descriptors),
                "growth": max(file_descriptors) - min(file_descriptors)
            },
            "threads": {
                "min": min(threads),
                "max": max(threads),
                "growth": max(threads) - min(threads)
            },
            "gc_objects": {
                "min": min(gc_objects),
                "max": max(gc_objects),
                "growth": max(gc_objects) - min(gc_objects)
            }
        }


class TestWebhookHandlerResourceUsage:
    """Resource usage tests for webhook handler under load."""
    
    def setup_method(self):
        """Set up resource usage test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.webhook_secret = "resource_test_secret"
        self.fake_uow = FakeUnitOfWork()
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
        self.resource_monitor = ResourceMonitor()
    
    async def test_webhook_processing_memory_efficiency(self):
        """Test memory efficiency of webhook processing under sustained load."""
        webhook_count = 500
        form_count = 5
        
        # Setup test forms
        form_ids = []
        for i in range(form_count):
            form_id = f"memory_test_form_{i}_{get_next_onboarding_form_id()}"
            form_ids.append(form_id)
            
            test_form = create_onboarding_form(
                typeform_id=form_id,
                webhook_url=f"https://test.example.com/webhook/{i}",
                name=f"Memory Test Form {i}"
            )
            await self.fake_uow.onboarding_forms.add(test_form)
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Process webhooks continuously
        processed_count = 0
        for i in range(webhook_count):
            form_id = form_ids[i % len(form_ids)]
            
            # Generate webhook payload and signature
            payload_json, headers = create_webhook_payload_with_signature(
                form_id, f"memory_test_{i}", self.webhook_secret
            )
            
            status_code, result = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=self.webhook_secret
            )
            
            if status_code == 200:
                processed_count += 1
            
            # Periodic garbage collection to test memory stability
            if i % 100 == 0:
                gc.collect()
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Memory efficiency assertions
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            max_memory = resource_summary["memory_rss_mb"]["max"]
            
            # Memory growth should be reasonable for the workload
            assert memory_growth < 200, f"Memory growth {memory_growth:.1f}MB should be < 200MB for {webhook_count} webhooks"
            
            # Memory usage should be stable (low variance)
            assert max_memory < 1000, f"Max memory usage {max_memory:.1f}MB should be reasonable"
            
            # GC object growth should be manageable
            gc_growth = resource_summary["gc_objects"]["growth"]
            assert gc_growth < webhook_count * 20, f"GC object growth {gc_growth} should be manageable"
        
        # Verify all webhooks were processed
        assert processed_count == webhook_count, f"Should process all {webhook_count} webhooks"
        
        # Verify data integrity
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert isinstance(stored_responses, list)
        assert len(stored_responses) == webhook_count
        
        print(f"✅ Webhook processing memory efficiency:")
        print(f"   Processed {processed_count} webhooks successfully")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory: {resource_summary['memory_rss_mb']['min']:.1f}MB → {resource_summary['memory_rss_mb']['max']:.1f}MB")
            print(f"   Memory growth: {resource_summary['memory_rss_mb']['growth']:.1f}MB")
            print(f"   GC objects growth: {resource_summary['gc_objects']['growth']}")
    
    async def test_concurrent_webhook_resource_consumption(self):
        """Test resource consumption under concurrent webhook processing."""
        concurrent_batches = 10
        webhooks_per_batch = 20
        total_webhooks = concurrent_batches * webhooks_per_batch
        
        # Setup test form
        form_id = f"concurrent_resource_form_{get_next_onboarding_form_id()}"
        test_form = create_onboarding_form(
            typeform_id=form_id,
            webhook_url="https://test.example.com/webhook",
            name="Concurrent Resource Test Form"
        )
        await self.fake_uow.onboarding_forms.add(test_form)
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        async def process_webhook_batch(batch_id: int) -> int:
            """Process a batch of webhooks concurrently."""
            successful_count = 0
            
            for i in range(webhooks_per_batch):
                # Generate webhook payload and signature
                payload_json, headers = create_webhook_payload_with_signature(
                    form_id, f"concurrent_test_{batch_id}_{i}", self.webhook_secret
                )
                
                try:
                    status_code, result = await self.webhook_handler.handle_webhook(
                        payload=payload_json,
                        headers=headers,
                        webhook_secret=self.webhook_secret
                    )
                    
                    if status_code == 200:
                        successful_count += 1
                except Exception:
                    # Continue processing other webhooks
                    pass
            
            return successful_count
        
        # Execute concurrent batches
        start_time = time.perf_counter()
        
        tasks = [process_webhook_batch(i) for i in range(concurrent_batches)]
        batch_results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        total_processed = sum(batch_results)
        processing_rate = total_processed / total_duration
        
        # Concurrent resource consumption assertions
        assert total_processed == total_webhooks, f"Should process all {total_webhooks} webhooks concurrently"
        assert processing_rate > 50, f"Concurrent processing rate {processing_rate:.1f}/s should be > 50/s"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            # Resource usage should remain reasonable under concurrency
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            cpu_max = resource_summary["cpu_percent"]["max"]
            thread_growth = resource_summary["threads"]["growth"]
            
            assert memory_growth < 300, f"Concurrent memory growth {memory_growth:.1f}MB should be < 300MB"
            assert cpu_max < 200, f"Max CPU usage {cpu_max:.1f}% should be reasonable"
            assert thread_growth < 50, f"Thread growth {thread_growth} should be manageable"
        
        print(f"✅ Concurrent webhook resource consumption:")
        print(f"   {total_processed} webhooks in {concurrent_batches} concurrent batches")
        print(f"   Processing rate: {processing_rate:.1f}/s")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory growth: {resource_summary['memory_rss_mb']['growth']:.1f}MB")
            print(f"   Max CPU: {resource_summary['cpu_percent']['max']:.1f}%")
            print(f"   Thread growth: {resource_summary['threads']['growth']}")
    
    async def test_long_running_webhook_resource_stability(self):
        """Test resource stability during long-running webhook processing."""
        test_duration_minutes = 3  # 3 minute long-running test
        webhook_interval = 0.5  # Process webhook every 500ms
        
        # Setup test form
        form_id = f"longrun_resource_form_{get_next_onboarding_form_id()}"
        test_form = create_onboarding_form(
            typeform_id=form_id,
            webhook_url="https://test.example.com/webhook",
            name="Long Running Resource Test Form"
        )
        await self.fake_uow.onboarding_forms.add(test_form)
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        start_time = time.perf_counter()
        processed_count = 0
        resource_snapshots = []
        
        while (time.perf_counter() - start_time) < (test_duration_minutes * 60):
            # Process webhook
            payload_json, headers = create_webhook_payload_with_signature(
                form_id, f"longrun_test_{processed_count}", self.webhook_secret
            )
            
            status_code, result = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=self.webhook_secret
            )
            
            if status_code == 200:
                processed_count += 1
            
            # Take resource snapshot every 30 seconds
            if processed_count % 60 == 0:  # Every ~30 seconds at 500ms intervals
                if PSUTIL_AVAILABLE and self.resource_monitor.process:
                    memory_info = self.resource_monitor.process.memory_info()
                    resource_snapshots.append({
                        "timestamp": time.perf_counter() - start_time,
                        "processed_count": processed_count,
                        "memory_rss_mb": memory_info.rss / 1024 / 1024,
                        "gc_objects": len(gc.get_objects())
                    })
                
                # Periodic garbage collection
                gc.collect()
            
            # Maintain processing interval
            await asyncio.sleep(webhook_interval)
        
        total_duration = time.perf_counter() - start_time
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Long-running stability assertions
        processing_rate = processed_count / total_duration
        assert processed_count > 0, "Should process webhooks during long run"
        assert processing_rate > 1, f"Processing rate {processing_rate:.1f}/s should be > 1/s"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            # Resource usage should be stable over time
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            
            assert memory_growth < 150, f"Long-running memory growth {memory_growth:.1f}MB should be < 150MB"
            
            # Analyze resource snapshots for stability
            if len(resource_snapshots) > 2:
                memory_values = [s["memory_rss_mb"] for s in resource_snapshots]
                memory_variance = statistics.variance(memory_values)
                
                assert memory_variance < 500, f"Memory variance {memory_variance:.1f} should be stable"
        
        print(f"✅ Long-running webhook resource stability:")
        print(f"   {processed_count} webhooks processed over {total_duration:.1f}s")
        print(f"   Processing rate: {processing_rate:.1f}/s")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory stability: {resource_summary['memory_rss_mb']['growth']:.1f}MB growth")
            print(f"   Resource snapshots: {len(resource_snapshots)}")


class TestRetryManagerResourceUsage:
    """Resource usage tests for webhook retry manager."""
    
    def setup_method(self):
        """Set up retry manager resource usage test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.retry_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=1,
            max_total_attempts=5
        )
        
        self.mock_executor = AsyncMock()
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.retry_policy,
            webhook_executor=self.mock_executor,
            metrics_collector=AsyncMock()
        )
        
        self.resource_monitor = ResourceMonitor()
    
    async def test_retry_queue_memory_scalability(self):
        """Test memory scalability of retry queue under large workloads."""
        large_queue_size = 5000  # 5000 pending retries
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Build up large retry queue
        webhook_ids = []
        for i in range(large_queue_size):
            webhook_id = f"scalability_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Scalability test"
            )
            
            # Periodic memory check
            if i % 1000 == 0:
                gc.collect()
        
        # Verify queue size
        assert len(self.retry_manager._retry_queue) == large_queue_size
        assert len(self.retry_manager._retry_records) == large_queue_size
        
        # Process some retries and measure cleanup efficiency
        processed_count = 0
        for webhook_id in webhook_ids[:1000]:  # Process first 1000
            retry_record = self.retry_manager._retry_records[webhook_id]
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        # Mock successful execution for cleanup
        self.mock_executor.return_value = {
            "status_code": 200,
            "success": True,
            "response_body": '{"status": "success"}'
        }
        
        results = await self.retry_manager.process_retry_queue()
        processed_count = results["processed"]
        
        # Clean up processed webhooks
        for webhook_id in webhook_ids[:processed_count]:
            if webhook_id in self.retry_manager._retry_records:
                del self.retry_manager._retry_records[webhook_id]
            if webhook_id in self.retry_manager._retry_queue:
                self.retry_manager._retry_queue.remove(webhook_id)
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Memory scalability assertions
        remaining_queue_size = len(self.retry_manager._retry_queue)
        expected_remaining = large_queue_size - processed_count
        
        assert remaining_queue_size <= expected_remaining, f"Queue cleanup should be effective"
        assert processed_count > 0, "Should process some retries"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            
            # Memory growth should be proportional to queue size
            max_acceptable_growth = large_queue_size * 0.05  # ~50KB per webhook (reasonable)
            assert memory_growth < max_acceptable_growth, f"Memory growth {memory_growth:.1f}MB should be proportional to queue size"
        
        print(f"✅ Retry queue memory scalability:")
        print(f"   Queue size: {large_queue_size} → {remaining_queue_size} (processed {processed_count})")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory growth: {resource_summary['memory_rss_mb']['growth']:.1f}MB")
    
    async def test_retry_scheduling_resource_efficiency(self):
        """Test resource efficiency of retry scheduling operations."""
        scheduling_count = 2000
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Measure scheduling performance and resource usage
        start_time = time.perf_counter()
        
        for i in range(scheduling_count):
            webhook_id = f"efficiency_{i}_{get_next_webhook_counter()}"
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Efficiency test"
            )
        
        scheduling_duration = time.perf_counter() - start_time
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Resource efficiency assertions
        scheduling_rate = scheduling_count / scheduling_duration
        assert scheduling_rate > 500, f"Scheduling rate {scheduling_rate:.1f}/s should be > 500/s"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            cpu_max = resource_summary["cpu_percent"]["max"]
            
            # Scheduling should be resource efficient
            assert memory_growth < 100, f"Scheduling memory growth {memory_growth:.1f}MB should be < 100MB"
            assert cpu_max < 150, f"Max CPU usage {cpu_max:.1f}% should be reasonable"
        
        print(f"✅ Retry scheduling resource efficiency:")
        print(f"   {scheduling_count} webhooks scheduled in {scheduling_duration:.2f}s ({scheduling_rate:.1f}/s)")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory growth: {resource_summary['memory_rss_mb']['growth']:.1f}MB")
            print(f"   Max CPU: {resource_summary['cpu_percent']['max']:.1f}%")


class TestTypeFormClientResourceUsage:
    """Resource usage tests for TypeForm client operations."""
    
    def setup_method(self):
        """Set up TypeForm client resource usage test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.fake_api = FakeTypeFormAPI()
        self.client = TypeFormClient(api_key="resource_test_key")
        self.client.client = create_fake_httpx_client(self.fake_api)
        self.resource_monitor = ResourceMonitor()
    
    @pytest.mark.slow
    async def test_typeform_api_operations_resource_efficiency(self):
        """Test resource efficiency of TypeForm API operations."""
        operation_count = 200
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Mix different API operations
        operations_performed = 0
        start_time = time.perf_counter()
        
        for i in range(operation_count):
            operation_type = i % 4  # Cycle through different operations
            
            try:
                if operation_type == 0:
                    # Get form operation
                    form_id = f"resource_form_{i}_{get_next_typeform_api_counter():03d}"
                    await self.client.get_form(form_id)
                elif operation_type == 1:
                    # List webhooks operation
                    form_id = f"resource_form_{i}_{get_next_typeform_api_counter():03d}"
                    await self.client.list_webhooks(form_id)
                elif operation_type == 2:
                    # Create webhook operation
                    form_id = f"resource_form_{i}_{get_next_typeform_api_counter():03d}"
                    await self.client.create_webhook(
                        form_id=form_id,
                        webhook_url=f"https://test.example.com/webhook/{i}",
                        tag=f"resource_test_{i}"
                    )
                else:
                    # Rate limit status check
                    await self.client.get_rate_limit_status()
                
                operations_performed += 1
                
            except Exception:
                # Continue with other operations even if some fail
                pass
        
        total_duration = time.perf_counter() - start_time
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Resource efficiency assertions
        operation_rate = operations_performed / total_duration
        assert operations_performed > 0, "Should perform some operations successfully"
        assert operation_rate > 2, f"Operation rate {operation_rate:.1f}/s should be > 2/s"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            
            # API operations should be memory efficient
            assert memory_growth < 50, f"API operations memory growth {memory_growth:.1f}MB should be < 50MB"
        
        print(f"✅ TypeForm API operations resource efficiency:")
        print(f"   {operations_performed} operations in {total_duration:.2f}s ({operation_rate:.1f}/s)")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory growth: {resource_summary['memory_rss_mb']['growth']:.1f}MB")
    
    async def test_rate_limiting_resource_overhead(self):
        """Test resource overhead of rate limiting enforcement."""
        rate_limited_operations = 100
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Perform operations that will be rate limited
        start_time = time.perf_counter()
        
        for i in range(rate_limited_operations):
            form_id = f"rate_limit_form_{i}_{get_next_typeform_api_counter():03d}"
            
            # This will trigger rate limiting (2 req/sec limit)
            await self.client.get_form(form_id)
        
        total_duration = time.perf_counter() - start_time
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Rate limiting resource overhead assertions
        expected_min_duration = (rate_limited_operations - 1) / 2.0  # 2 req/sec
        actual_rate = rate_limited_operations / total_duration
        
        # Should respect rate limiting
        assert total_duration >= expected_min_duration * 0.9, f"Should respect rate limiting timing"
        assert actual_rate <= 2.5, f"Actual rate {actual_rate:.1f}/s should be close to limit (2/s)"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            
            # Rate limiting should not add significant memory overhead
            assert memory_growth < 30, f"Rate limiting memory overhead {memory_growth:.1f}MB should be < 30MB"
        
        print(f"✅ Rate limiting resource overhead:")
        print(f"   {rate_limited_operations} operations in {total_duration:.2f}s ({actual_rate:.1f}/s)")
        print(f"   Expected duration: ≥{expected_min_duration:.1f}s (rate limited)")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory overhead: {resource_summary['memory_rss_mb']['growth']:.1f}MB")


class TestIntegratedSystemResourceUsage:
    """Resource usage tests for integrated system components."""
    
    def setup_method(self):
        """Set up integrated system resource usage test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.webhook_secret = "integrated_test_secret"
        self.fake_uow = FakeUnitOfWork()
        
        # Setup webhook handler
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
        
        # Setup retry manager
        self.retry_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=1,
            max_total_attempts=3
        )
        self.mock_executor = AsyncMock()
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.retry_policy,
            webhook_executor=self.mock_executor,
            metrics_collector=AsyncMock()
        )
        
        # Setup TypeForm client
        self.fake_api = FakeTypeFormAPI()
        self.typeform_client = TypeFormClient(api_key="integrated_test_key")
        self.typeform_client.client = create_fake_httpx_client(self.fake_api)
        
        self.resource_monitor = ResourceMonitor()
    
    async def test_integrated_system_resource_efficiency(self):
        """Test resource efficiency of integrated system under realistic load."""
        integrated_test_duration = 60  # 1 minute integrated test
        webhook_frequency = 5  # 5 webhooks per second
        
        # Setup test forms
        form_count = 3
        form_ids = []
        for i in range(form_count):
            form_id = f"integrated_form_{i}_{get_next_onboarding_form_id()}"
            form_ids.append(form_id)
            
            test_form = create_onboarding_form(
                typeform_id=form_id,
                webhook_url=f"https://test.example.com/webhook/{i}",
                name=f"Integrated Test Form {i}"
            )
            await self.fake_uow.onboarding_forms.add(test_form)
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Run integrated system test
        start_time = time.perf_counter()
        webhook_count = 0
        retry_count = 0
        api_operations = 0
        
        while (time.perf_counter() - start_time) < integrated_test_duration:
            cycle_start = time.perf_counter()
            
            # Process webhooks
            for _ in range(webhook_frequency):
                form_id = form_ids[webhook_count % len(form_ids)]
                
                payload_json, headers = create_webhook_payload_with_signature(
                    form_id, f"integrated_test_{webhook_count}", self.webhook_secret
                )
                
                try:
                    status_code, result = await self.webhook_handler.handle_webhook(
                        payload=payload_json,
                        headers=headers,
                        webhook_secret=self.webhook_secret
                    )
                    webhook_count += 1
                except Exception:
                    pass
            
            # Schedule some retries (simulate failures)
            if webhook_count % 20 == 0:  # Every 20 webhooks
                webhook_id = f"integrated_retry_{retry_count}_{get_next_webhook_counter()}"
                
                await self.retry_manager.schedule_webhook_retry(
                    webhook_id=webhook_id,
                    form_id=form_ids[retry_count % len(form_ids)],
                    webhook_url="https://api.example.com/webhook",
                    initial_failure_reason="Integrated test failure"
                )
                retry_count += 1
            
            # Perform TypeForm API operations
            if webhook_count % 10 == 0:  # Every 10 webhooks
                try:
                    form_id = f"api_test_{api_operations}_{get_next_typeform_api_counter():03d}"
                    await self.typeform_client.get_form(form_id)
                    api_operations += 1
                except Exception:
                    pass
            
            # Maintain frequency
            cycle_duration = time.perf_counter() - cycle_start
            sleep_time = max(0, 1.0 - cycle_duration)  # Target 1 second cycles
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        total_duration = time.perf_counter() - start_time
        
        # Stop monitoring and analyze
        resource_summary = self.resource_monitor.stop_monitoring()
        
        # Integrated system efficiency assertions
        webhook_rate = webhook_count / total_duration
        
        assert webhook_count > 0, "Should process webhooks in integrated test"
        assert retry_count > 0, "Should schedule some retries"
        assert api_operations > 0, "Should perform API operations"
        
        # Performance should be reasonable under integrated load
        assert webhook_rate > 3, f"Webhook processing rate {webhook_rate:.1f}/s should be > 3/s"
        
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            memory_growth = resource_summary["memory_rss_mb"]["growth"]
            cpu_max = resource_summary["cpu_percent"]["max"]
            
            # Integrated system should be resource efficient
            assert memory_growth < 200, f"Integrated memory growth {memory_growth:.1f}MB should be < 200MB"
            assert cpu_max < 200, f"Max CPU usage {cpu_max:.1f}% should be reasonable"
        
        print(f"✅ Integrated system resource efficiency:")
        print(f"   Test duration: {total_duration:.1f}s")
        print(f"   Webhooks processed: {webhook_count} ({webhook_rate:.1f}/s)")
        print(f"   Retries scheduled: {retry_count}")
        print(f"   API operations: {api_operations}")
        if PSUTIL_AVAILABLE and resource_summary.get("memory_rss_mb"):
            print(f"   Memory growth: {resource_summary['memory_rss_mb']['growth']:.1f}MB")
            print(f"   Max CPU: {resource_summary['cpu_percent']['max']:.1f}%")