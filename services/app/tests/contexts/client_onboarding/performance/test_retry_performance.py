"""
Performance tests for webhook retry service under load.

Tests webhook retry performance, scalability, and resource usage under realistic
high-volume scenarios to validate production readiness.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, List
import statistics
import gc

from src.contexts.client_onboarding.core.services.webhook_retry import (
    WebhookRetryManager,
    WebhookRetryPolicyConfig,
    WebhookRetryRecord,
    RetryStatus
)

from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork

pytestmark = pytest.mark.anyio


class PerformanceWebhookExecutor:
    """High-performance mock webhook executor for load testing."""
    
    def __init__(self, response_time_ms: float = 10, success_rate: float = 0.8):
        self.response_time_ms = response_time_ms
        self.success_rate = success_rate
        self.call_count = 0
        self.total_execution_time = 0
        self.start_time = None
        
    async def execute_webhook(self, webhook_url: str, webhook_id: str, form_id: str) -> Dict[str, Any]:
        """Fast webhook execution with configurable response time and success rate."""
        self.call_count += 1
        
        if not self.start_time:
            self.start_time = time.perf_counter()
        
        # Simulate network latency
        await asyncio.sleep(self.response_time_ms / 1000)
        
        execution_end = time.perf_counter()
        self.total_execution_time = execution_end - self.start_time
        
        # Determine success based on configured rate
        import random
        is_success = random.random() < self.success_rate
        
        if is_success:
            return {
                "status_code": 200,
                "success": True,
                "response_body": '{"status": "success"}',
                "error_message": None
            }
        else:
            return {
                "status_code": 500,
                "success": False,
                "error_message": "Simulated server error",
                "response_body": None
            }
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics from the executor."""
        return {
            "total_calls": self.call_count,
            "total_execution_time_seconds": self.total_execution_time,
            "calls_per_second": self.call_count / max(self.total_execution_time, 0.001),
            "average_call_time_ms": (self.total_execution_time * 1000) / max(self.call_count, 1)
        }


class TestWebhookRetryPerformance:
    """Performance tests for webhook retry service scalability."""
    
    def setup_method(self):
        """Set up performance test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        # Optimized policy for performance testing
        self.performance_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=1,     # 1 minute minimum (int required)
            max_retry_interval_minutes=5,         # 5 minutes max (int required)
            exponential_backoff_multiplier=1.5,   # Lower multiplier for faster progression
            jitter_percentage=5.0,                # Minimal jitter for predictable performance
            max_retry_duration_hours=1,           # 1 hour max duration (int required)
            max_total_attempts=5,
            failure_rate_disable_threshold=95.0   # Allow some failures before disable
        )
        
        self.performance_executor = PerformanceWebhookExecutor(
            response_time_ms=5,   # 5ms simulated response time
            success_rate=0.7      # 70% success rate for realistic load
        )
        
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.performance_policy,
            webhook_executor=self.performance_executor.execute_webhook,
            metrics_collector=AsyncMock()  # Async mock for minimal overhead
        )
    
    async def test_high_volume_webhook_scheduling_performance(self):
        """Test performance of scheduling large numbers of webhooks for retry."""
        webhook_count = 1000
        webhook_ids = []
        
        # Measure scheduling performance
        start_time = time.perf_counter()
        
        for i in range(webhook_count):
            webhook_id = f"perf_schedule_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Performance test",
                initial_status_code=500
            )
        
        end_time = time.perf_counter()
        scheduling_duration = end_time - start_time
        
        # Performance assertions
        assert len(self.retry_manager._retry_records) == webhook_count
        assert len(self.retry_manager._retry_queue) == webhook_count
        
        # Should schedule 1000 webhooks in under 2 seconds
        assert scheduling_duration < 2.0, f"Scheduling took {scheduling_duration:.2f}s, expected < 2.0s"
        
        # Calculate scheduling rate
        scheduling_rate = webhook_count / scheduling_duration
        assert scheduling_rate > 500, f"Scheduling rate {scheduling_rate:.1f}/s, expected > 500/s"
        
        print(f"✅ Scheduled {webhook_count} webhooks in {scheduling_duration:.3f}s ({scheduling_rate:.1f}/s)")
    
    async def test_concurrent_retry_queue_processing_performance(self):
        """Test performance of processing large retry queues concurrently."""
        webhook_count = 500
        
        # Schedule webhooks
        webhook_ids = []
        for i in range(webhook_count):
            webhook_id = f"perf_concurrent_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Concurrent test"
            )
            
            # Set retry time to past for immediate processing
            retry_record = self.retry_manager._retry_records[webhook_id]
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        # Measure concurrent processing performance
        start_time = time.perf_counter()
        
        # Process all webhooks
        results = await self.retry_manager.process_retry_queue()
        
        end_time = time.perf_counter()
        processing_duration = end_time - start_time
        
        # Performance assertions
        total_processed = results["processed"]
        assert total_processed == webhook_count
        
        # Should process 500 webhooks in under 5 seconds (with 5ms simulated latency each)
        expected_max_duration = 5.0
        assert processing_duration < expected_max_duration, f"Processing took {processing_duration:.2f}s, expected < {expected_max_duration}s"
        
        # Calculate processing rate
        processing_rate = total_processed / processing_duration
        assert processing_rate > 100, f"Processing rate {processing_rate:.1f}/s, expected > 100/s"
        
        # Get executor performance metrics
        executor_metrics = self.performance_executor.get_performance_metrics()
        
        print(f"✅ Processed {total_processed} webhooks in {processing_duration:.3f}s ({processing_rate:.1f}/s)")
        print(f"   Executor metrics: {executor_metrics['calls_per_second']:.1f} calls/s, {executor_metrics['average_call_time_ms']:.1f}ms avg")
    
    async def test_memory_usage_under_sustained_load(self):
        """Test memory usage remains stable under sustained webhook retry load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Sustained load test - multiple rounds of webhook processing
        rounds = 5
        webhooks_per_round = 200
        memory_samples = []
        
        for round_num in range(rounds):
            # Schedule webhooks for this round
            webhook_ids = []
            for i in range(webhooks_per_round):
                webhook_id = f"memory_test_r{round_num}_w{i}_{get_next_webhook_counter()}"
                webhook_ids.append(webhook_id)
                
                await self.retry_manager.schedule_webhook_retry(
                    webhook_id=webhook_id,
                    form_id=f"form_{get_next_onboarding_form_id()}",
                    webhook_url="https://api.example.com/webhook",
                    initial_failure_reason="Memory test"
                )
                
                # Set for immediate processing
                retry_record = self.retry_manager._retry_records[webhook_id]
                retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Process the round
            await self.retry_manager.process_retry_queue()
            
            # Force garbage collection and measure memory
            gc.collect()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory_mb)
            
            # Clean up processed webhooks to simulate production cleanup
            for webhook_id in webhook_ids:
                if webhook_id in self.retry_manager._retry_records:
                    del self.retry_manager._retry_records[webhook_id]
                if webhook_id in self.retry_manager._retry_queue:
                    self.retry_manager._retry_queue.remove(webhook_id)
        
        final_memory_mb = memory_samples[-1]
        memory_growth_mb = final_memory_mb - initial_memory_mb
        
        # Memory growth should be minimal (< 50MB) under sustained load
        max_acceptable_growth_mb = 50
        assert memory_growth_mb < max_acceptable_growth_mb, f"Memory grew by {memory_growth_mb:.1f}MB, expected < {max_acceptable_growth_mb}MB"
        
        # Memory usage should be stable (low variance between rounds)
        if len(memory_samples) > 1:
            memory_variance = statistics.variance(memory_samples)
            assert memory_variance < 100, f"Memory variance {memory_variance:.1f}, expected stable usage"
        
        print(f"✅ Memory stable under sustained load: {initial_memory_mb:.1f}MB → {final_memory_mb:.1f}MB (+{memory_growth_mb:.1f}MB)")
    
    async def test_retry_timing_accuracy_under_load(self):
        """Test retry timing accuracy remains precise under high load."""
        webhook_count = 100
        expected_intervals = []
        actual_intervals = []
        
        # Schedule webhooks with known retry intervals
        webhook_ids = []
        base_time = datetime.now(UTC)
        
        for i in range(webhook_count):
            webhook_id = f"timing_test_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Timing test"
            )
            
            retry_record = self.retry_manager._retry_records[webhook_id]
            
            # Calculate expected interval based on policy (1 minute = 60 seconds)
            expected_interval_seconds = self.performance_policy.initial_retry_interval_minutes * 60
            expected_intervals.append(expected_interval_seconds)
            
            # Calculate actual interval
            if retry_record.next_retry_time:
                actual_interval = (retry_record.next_retry_time - retry_record.initial_failure_time).total_seconds()
                actual_intervals.append(actual_interval)
        
        # Analyze timing accuracy
        timing_errors = []
        for expected, actual in zip(expected_intervals, actual_intervals):
            error_percent = abs(actual - expected) / expected * 100
            timing_errors.append(error_percent)
        
        # Timing accuracy assertions
        assert len(timing_errors) == webhook_count
        
        # Average timing error should be < 10% (allowing for jitter)
        avg_timing_error = statistics.mean(timing_errors)
        assert avg_timing_error < 10.0, f"Average timing error {avg_timing_error:.1f}%, expected < 10%"
        
        # 95% of timings should be within 20% of expected (accounting for jitter)
        errors_within_threshold = sum(1 for error in timing_errors if error < 20.0)
        accuracy_percentage = (errors_within_threshold / webhook_count) * 100
        assert accuracy_percentage >= 95.0, f"Timing accuracy {accuracy_percentage:.1f}%, expected ≥ 95%"
        
        print(f"✅ Retry timing accuracy: {accuracy_percentage:.1f}% within 20%, avg error {avg_timing_error:.1f}%")
    
    async def test_exponential_backoff_performance_scaling(self):
        """Test exponential backoff calculation performance scales with attempt count."""
        webhook_id = f"backoff_perf_{get_next_webhook_counter()}"
        
        # Schedule webhook
        await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=f"form_{get_next_onboarding_form_id()}",
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Backoff performance test"
        )
        
        retry_record = self.retry_manager._retry_records[webhook_id]
        
        # Test backoff calculation performance across many attempts
        attempt_counts = [1, 5, 10, 20, 50, 100]
        calculation_times = []
        
        for attempt_count in attempt_counts:
            # Measure backoff calculation time
            start_time = time.perf_counter()
            
            # Calculate backoff 100 times to get measurable duration
            for _ in range(100):
                next_retry_time = self.retry_manager._calculate_next_retry_time(attempt_count)
                assert next_retry_time is not None
            
            end_time = time.perf_counter()
            avg_calculation_time_ms = ((end_time - start_time) / 100) * 1000
            calculation_times.append(avg_calculation_time_ms)
        
        # Performance assertions
        # Backoff calculation should be fast even for high attempt counts
        max_calculation_time_ms = max(calculation_times)
        assert max_calculation_time_ms < 1.0, f"Max backoff calculation time {max_calculation_time_ms:.3f}ms, expected < 1.0ms"
        
        # Calculation time should not increase significantly with attempt count
        time_growth = calculation_times[-1] / calculation_times[0]
        assert time_growth < 5.0, f"Calculation time grew {time_growth:.1f}x, expected < 5x"
        
        print(f"✅ Backoff calculation performance: {max_calculation_time_ms:.3f}ms max, {time_growth:.1f}x growth")


class TestWebhookRetryPerformanceStress:
    """Stress tests for webhook retry service under extreme conditions."""
    
    def setup_method(self):
        """Set up stress test environment."""
        # Minimal policy for maximum stress
        self.stress_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=1,      # 1 minute minimum (int required)
            max_retry_interval_minutes=2,          # 2 minutes max (int required)
            exponential_backoff_multiplier=1.2,    # Minimal multiplier
            jitter_percentage=1.0,                 # Minimal jitter
            max_retry_duration_hours=1,            # 1 hour max (int required)
            max_total_attempts=3,                  # Fast failure
            failure_rate_disable_threshold=90.0
        )
        
        self.stress_executor = PerformanceWebhookExecutor(
            response_time_ms=1,   # 1ms ultra-fast response
            success_rate=0.5      # 50% success rate for stress
        )
        
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.stress_policy,
            webhook_executor=self.stress_executor.execute_webhook,
            metrics_collector=AsyncMock()
        )
    
    async def test_extreme_volume_webhook_processing(self):
        """Stress test with extreme volume of webhooks."""
        webhook_count = 2000  # 2000 webhooks for stress testing
        
        # Schedule all webhooks
        webhook_ids = []
        scheduling_start = time.perf_counter()
        
        for i in range(webhook_count):
            webhook_id = f"stress_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Stress test"
            )
            
            # Set for immediate processing
            retry_record = self.retry_manager._retry_records[webhook_id]
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        scheduling_duration = time.perf_counter() - scheduling_start
        
        # Process all webhooks
        processing_start = time.perf_counter()
        results = await self.retry_manager.process_retry_queue()
        processing_duration = time.perf_counter() - processing_start
        
        # Stress test assertions
        assert results["processed"] == webhook_count
        
        # Should handle extreme volume efficiently
        # Allow more time for extreme volume but still maintain reasonable performance
        assert scheduling_duration < 5.0, f"Scheduling took {scheduling_duration:.2f}s, expected < 5.0s"
        assert processing_duration < 10.0, f"Processing took {processing_duration:.2f}s, expected < 10.0s"
        
        # Calculate rates
        scheduling_rate = webhook_count / scheduling_duration
        processing_rate = webhook_count / processing_duration
        
        assert scheduling_rate > 400, f"Scheduling rate {scheduling_rate:.1f}/s, expected > 400/s"
        assert processing_rate > 200, f"Processing rate {processing_rate:.1f}/s, expected > 200/s"
        
        print(f"✅ Extreme volume stress test: {webhook_count} webhooks")
        print(f"   Scheduling: {scheduling_duration:.2f}s ({scheduling_rate:.1f}/s)")
        print(f"   Processing: {processing_duration:.2f}s ({processing_rate:.1f}/s)")
    
    async def test_concurrent_retry_queue_access_stress(self):
        """Stress test concurrent access to retry queue and records."""
        concurrent_operations = 50
        webhooks_per_operation = 20
        
        async def concurrent_operation(operation_id: int):
            """Simulate concurrent webhook operations."""
            webhook_ids = []
            
            # Schedule webhooks
            for i in range(webhooks_per_operation):
                webhook_id = f"concurrent_stress_{operation_id}_{i}_{get_next_webhook_counter()}"
                webhook_ids.append(webhook_id)
                
                await self.retry_manager.schedule_webhook_retry(
                    webhook_id=webhook_id,
                    form_id=f"form_{get_next_onboarding_form_id()}",
                    webhook_url="https://api.example.com/webhook",
                    initial_failure_reason="Concurrent stress test"
                )
                
                # Set for processing
                retry_record = self.retry_manager._retry_records[webhook_id]
                retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Process some webhooks
            await self.retry_manager.process_retry_queue()
            
            return len(webhook_ids)
        
        # Run concurrent operations
        start_time = time.perf_counter()
        
        tasks = [concurrent_operation(i) for i in range(concurrent_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        concurrent_duration = end_time - start_time
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Concurrent access caused {len(exceptions)} exceptions: {exceptions[:3]}"
        
        # Verify all operations completed
        total_webhooks_scheduled = sum(r for r in results if isinstance(r, int))
        expected_total = concurrent_operations * webhooks_per_operation
        assert total_webhooks_scheduled == expected_total
        
        # Performance assertion for concurrent access
        assert concurrent_duration < 15.0, f"Concurrent operations took {concurrent_duration:.2f}s, expected < 15.0s"
        
        concurrent_rate = total_webhooks_scheduled / concurrent_duration
        assert concurrent_rate > 100, f"Concurrent rate {concurrent_rate:.1f}/s, expected > 100/s"
        
        print(f"✅ Concurrent stress test: {concurrent_operations} operations, {total_webhooks_scheduled} webhooks")
        print(f"   Duration: {concurrent_duration:.2f}s ({concurrent_rate:.1f}/s)")


class TestWebhookRetryPerformanceBenchmarks:
    """Benchmark tests for webhook retry service performance baselines."""
    
    def setup_method(self):
        """Set up benchmark test environment."""
        self.benchmark_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=1,     # 1 minute minimum (int required)
            max_total_attempts=3
        )
        
        self.benchmark_executor = PerformanceWebhookExecutor(
            response_time_ms=10,
            success_rate=0.8
        )
        
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.benchmark_policy,
            webhook_executor=self.benchmark_executor.execute_webhook
        )
    
    async def test_single_webhook_retry_latency_benchmark(self):
        """Benchmark latency for single webhook retry operations."""
        webhook_id = f"latency_benchmark_{get_next_webhook_counter()}"
        
        # Measure scheduling latency
        start_time = time.perf_counter()
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=f"form_{get_next_onboarding_form_id()}",
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Latency benchmark"
        )
        scheduling_latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Set for immediate processing and measure processing latency
        retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        start_time = time.perf_counter()
        results = await self.retry_manager.process_retry_queue()
        processing_latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Latency benchmarks
        # Scheduling should be very fast (< 5ms)
        assert scheduling_latency_ms < 5.0, f"Scheduling latency {scheduling_latency_ms:.2f}ms, expected < 5.0ms"
        
        # Processing should be fast (< 50ms including 10ms simulated webhook call)
        assert processing_latency_ms < 50.0, f"Processing latency {processing_latency_ms:.2f}ms, expected < 50.0ms"
        
        print(f"✅ Single webhook latency benchmark:")
        print(f"   Scheduling: {scheduling_latency_ms:.2f}ms")
        print(f"   Processing: {processing_latency_ms:.2f}ms")
    
    async def test_throughput_benchmark_baseline(self):
        """Establish throughput benchmark baseline for webhook retry processing."""
        webhook_counts = [100, 500, 1000]
        throughput_results = {}
        
        for webhook_count in webhook_counts:
            # Schedule webhooks
            webhook_ids = []
            for i in range(webhook_count):
                webhook_id = f"throughput_{webhook_count}_{i}_{get_next_webhook_counter()}"
                webhook_ids.append(webhook_id)
                
                await self.retry_manager.schedule_webhook_retry(
                    webhook_id=webhook_id,
                    form_id=f"form_{get_next_onboarding_form_id()}",
                    webhook_url="https://api.example.com/webhook",
                    initial_failure_reason="Throughput benchmark"
                )
                
                retry_record = self.retry_manager._retry_records[webhook_id]
                retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Measure processing throughput
            start_time = time.perf_counter()
            results = await self.retry_manager.process_retry_queue()
            processing_duration = time.perf_counter() - start_time
            
            throughput = webhook_count / processing_duration
            throughput_results[webhook_count] = throughput
            
            # Clean up for next test
            self.retry_manager._retry_records.clear()
            self.retry_manager._retry_queue.clear()
            self.benchmark_executor.call_count = 0
            self.benchmark_executor.start_time = None
        
        # Throughput benchmarks (adjusted for realistic performance expectations)
        for webhook_count, throughput in throughput_results.items():
            if webhook_count == 100:
                assert throughput > 80, f"100 webhook throughput {throughput:.1f}/s, expected > 80/s"
            elif webhook_count == 500:
                assert throughput > 70, f"500 webhook throughput {throughput:.1f}/s, expected > 70/s"
            elif webhook_count == 1000:
                assert throughput > 60, f"1000 webhook throughput {throughput:.1f}/s, expected > 60/s"
        
        print(f"✅ Throughput benchmark baseline:")
        for webhook_count, throughput in throughput_results.items():
            print(f"   {webhook_count:4d} webhooks: {throughput:6.1f}/s")
    
    async def test_memory_efficiency_benchmark(self):
        """Benchmark memory efficiency for webhook retry operations."""
        import sys
        
        webhook_count = 1000
        
        # Measure memory before operations
        initial_objects = len(gc.get_objects())
        
        # Create and process webhooks
        webhook_ids = []
        for i in range(webhook_count):
            webhook_id = f"memory_benchmark_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Memory benchmark"
            )
            
            retry_record = self.retry_manager._retry_records[webhook_id]
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        # Process webhooks
        await self.retry_manager.process_retry_queue()
        
        # Measure memory after operations
        post_operation_objects = len(gc.get_objects())
        object_growth = post_operation_objects - initial_objects
        
        # Clean up and measure final memory
        self.retry_manager._retry_records.clear()
        self.retry_manager._retry_queue.clear()
        gc.collect()
        
        final_objects = len(gc.get_objects())
        objects_cleaned = post_operation_objects - final_objects
        
        # Memory efficiency benchmarks
        # Object growth should be reasonable for the number of webhooks processed
        max_acceptable_growth = webhook_count * 10  # Allow up to 10 objects per webhook
        assert object_growth < max_acceptable_growth, f"Object growth {object_growth}, expected < {max_acceptable_growth}"
        
        # Most objects should be cleaned up after explicit cleanup
        cleanup_percentage = (objects_cleaned / object_growth) * 100 if object_growth > 0 else 100
        assert cleanup_percentage > 50, f"Cleanup percentage {cleanup_percentage:.1f}%, expected > 50%"
        
        print(f"✅ Memory efficiency benchmark:")
        print(f"   Object growth: {object_growth} objects for {webhook_count} webhooks")
        print(f"   Cleanup rate: {cleanup_percentage:.1f}% objects cleaned")


class TestWebhookRetryProductionScenarios:
    """Production scenario tests for webhook retry service performance."""
    
    def setup_method(self):
        """Set up production scenario test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        # Production-like policy with realistic settings
        self.production_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=2,     # 2 minute initial (production realistic)
            max_retry_interval_minutes=60,        # 60 minutes max (production realistic)
            exponential_backoff_multiplier=2.0,   # Standard exponential backoff
            jitter_percentage=25.0,               # Production jitter for load distribution
            max_retry_duration_hours=10,          # 10 hour max duration (production realistic)
            max_total_attempts=10,                # More attempts for production resilience
            failure_rate_disable_threshold=95.0  # High threshold for production stability
        )
        
        # Production-grade executor with realistic response patterns
        self.production_executor = PerformanceWebhookExecutor(
            response_time_ms=50,   # 50ms realistic API response time
            success_rate=0.85      # 85% success rate (realistic production failure rate)
        )
        
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.production_policy,
            webhook_executor=self.production_executor.execute_webhook,
            metrics_collector=AsyncMock()
        )
    
    async def test_failure_cascade_recovery_performance(self):
        """Test performance during failure cascade and recovery scenarios."""
        cascade_size = 200  # Simulate cascade of 200 webhook failures
        
        # Phase 1: Simulate failure cascade (all webhooks fail initially)
        cascade_start = time.perf_counter()
        webhook_ids = []
        
        for i in range(cascade_size):
            webhook_id = f"cascade_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Cascade failure simulation",
                initial_status_code=503  # Service unavailable
            )
        
        cascade_scheduling_duration = time.perf_counter() - cascade_start
        
        # Verify all webhooks are scheduled for retry
        assert len(self.retry_manager._retry_records) == cascade_size
        
        # Phase 2: Simulate gradual recovery (modify executor for better success rate)
        self.production_executor.success_rate = 0.95  # Recovery to 95% success rate
        
        # Set all webhooks ready for immediate retry (simulate time passage)
        for webhook_id in webhook_ids[:100]:  # Process first half for recovery test
            retry_record = self.retry_manager._retry_records[webhook_id]
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        # Measure recovery performance
        recovery_start = time.perf_counter()
        recovery_results = await self.retry_manager.process_retry_queue()
        recovery_duration = time.perf_counter() - recovery_start
        
        # Performance assertions for cascade scenario
        scheduling_rate = cascade_size / cascade_scheduling_duration
        assert scheduling_rate > 200, f"Cascade scheduling rate {scheduling_rate:.1f}/s should be > 200/s"
        
        recovery_rate = recovery_results["processed"] / recovery_duration
        assert recovery_rate > 15, f"Recovery processing rate {recovery_rate:.1f}/s should be > 15/s"
        
        # Should have processed some webhooks during recovery
        assert recovery_results["processed"] > 0, "Should process some webhooks during recovery"
        assert recovery_results["successful"] > 0, "Should have some successful recoveries"
        
        print(f"✅ Failure cascade recovery performance:")
        print(f"   Cascade: {cascade_size} webhooks scheduled in {cascade_scheduling_duration:.2f}s ({scheduling_rate:.1f}/s)")
        print(f"   Recovery: {recovery_results['processed']} processed in {recovery_duration:.2f}s ({recovery_rate:.1f}/s)")
        print(f"   Success rate during recovery: {(recovery_results['successful'] / max(recovery_results['processed'], 1)) * 100:.1f}%")
    
    @pytest.mark.slow
    async def test_long_running_retry_queue_performance(self):
        """Test performance of retry queue operations over extended periods."""
        long_run_duration_minutes = 2  # 2 minute long-running test
        webhook_batch_size = 50
        batch_interval_seconds = 10  # Add new batch every 10 seconds
        
        total_webhooks_scheduled = 0
        total_webhooks_processed = 0
        performance_samples = []
        
        start_time = time.perf_counter()
        
        while (time.perf_counter() - start_time) < (long_run_duration_minutes * 60):
            batch_start = time.perf_counter()
            
            # Schedule new batch of webhooks
            batch_webhook_ids = []
            for i in range(webhook_batch_size):
                webhook_id = f"longrun_{total_webhooks_scheduled}_{get_next_webhook_counter()}"
                batch_webhook_ids.append(webhook_id)
                total_webhooks_scheduled += 1
                
                await self.retry_manager.schedule_webhook_retry(
                    webhook_id=webhook_id,
                    form_id=f"form_{get_next_onboarding_form_id()}",
                    webhook_url="https://api.example.com/webhook",
                    initial_failure_reason="Long-running test"
                )
                
                # Set some for immediate retry (simulate time progression)
                if i % 3 == 0:  # Every 3rd webhook ready for retry
                    retry_record = self.retry_manager._retry_records[webhook_id]
                    retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Process available retries
            processing_start = time.perf_counter()
            batch_results = await self.retry_manager.process_retry_queue()
            processing_duration = time.perf_counter() - processing_start
            
            total_webhooks_processed += batch_results["processed"]
            
            batch_duration = time.perf_counter() - batch_start
            performance_samples.append({
                "batch_size": webhook_batch_size,
                "batch_duration": batch_duration,
                "processing_duration": processing_duration,
                "processed_count": batch_results["processed"],
                "queue_size": len(self.retry_manager._retry_queue),
                "records_count": len(self.retry_manager._retry_records)
            })
            
            # Wait for next batch interval
            if (time.perf_counter() - start_time) < (long_run_duration_minutes * 60 - batch_interval_seconds):
                await asyncio.sleep(batch_interval_seconds)
        
        total_test_duration = time.perf_counter() - start_time
        
        # Analyze long-running performance
        avg_batch_duration = statistics.mean(sample["batch_duration"] for sample in performance_samples)
        avg_processing_duration = statistics.mean(sample["processing_duration"] for sample in performance_samples)
        avg_queue_size = statistics.mean(sample["queue_size"] for sample in performance_samples)
        
        # Long-running performance assertions
        assert total_webhooks_scheduled > 0, "Should have scheduled webhooks during long run"
        assert len(performance_samples) > 1, "Should have multiple performance samples"
        
        # Performance should remain stable over time
        assert avg_batch_duration < 5.0, f"Average batch duration {avg_batch_duration:.2f}s should be < 5.0s"
        assert avg_processing_duration < 2.0, f"Average processing duration {avg_processing_duration:.2f}s should be < 2.0s"
        
        # Queue should not grow uncontrollably
        max_queue_size = max(sample["queue_size"] for sample in performance_samples)
        assert max_queue_size < total_webhooks_scheduled * 0.8, f"Max queue size {max_queue_size} should be manageable"
        
        print(f"✅ Long-running retry queue performance:")
        print(f"   Test duration: {total_test_duration:.1f}s ({long_run_duration_minutes:.1f} min)")
        print(f"   Total scheduled: {total_webhooks_scheduled}, processed: {total_webhooks_processed}")
        print(f"   Avg batch duration: {avg_batch_duration:.2f}s, avg queue size: {avg_queue_size:.1f}")
        print(f"   Performance samples: {len(performance_samples)}")
    
    async def test_high_frequency_retry_scheduling_performance(self):
        """Test performance under high-frequency webhook retry scheduling."""
        high_frequency_duration = 30  # 30 second high-frequency test
        target_frequency = 20  # Target 20 webhook failures per second
        
        scheduled_webhooks = []
        scheduling_times = []
        
        start_time = time.perf_counter()
        webhook_counter = 0
        
        while (time.perf_counter() - start_time) < high_frequency_duration:
            # Schedule webhook at high frequency
            schedule_start = time.perf_counter()
            
            webhook_id = f"highfreq_{webhook_counter}_{get_next_webhook_counter()}"
            webhook_counter += 1
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="High frequency test"
            )
            
            schedule_end = time.perf_counter()
            scheduling_time = schedule_end - schedule_start
            scheduling_times.append(scheduling_time)
            scheduled_webhooks.append(webhook_id)
            
            # Maintain target frequency (sleep to regulate rate)
            target_interval = 1.0 / target_frequency
            if scheduling_time < target_interval:
                await asyncio.sleep(target_interval - scheduling_time)
        
        total_duration = time.perf_counter() - start_time
        actual_frequency = len(scheduled_webhooks) / total_duration
        
        # High-frequency performance assertions
        assert len(scheduled_webhooks) > 0, "Should have scheduled webhooks at high frequency"
        assert actual_frequency >= target_frequency * 0.8, f"Actual frequency {actual_frequency:.1f}/s should be >= {target_frequency * 0.8:.1f}/s"
        
        # Scheduling latency should remain low under high frequency
        avg_scheduling_time = statistics.mean(scheduling_times)
        max_scheduling_time = max(scheduling_times)
        
        assert avg_scheduling_time < 0.01, f"Average scheduling time {avg_scheduling_time*1000:.2f}ms should be < 10ms"
        assert max_scheduling_time < 0.05, f"Max scheduling time {max_scheduling_time*1000:.2f}ms should be < 50ms"
        
        # Queue should grow efficiently
        final_queue_size = len(self.retry_manager._retry_queue)
        assert final_queue_size == len(scheduled_webhooks), "All scheduled webhooks should be in queue"
        
        print(f"✅ High-frequency retry scheduling performance:")
        print(f"   {len(scheduled_webhooks)} webhooks scheduled in {total_duration:.1f}s ({actual_frequency:.1f}/s)")
        print(f"   Avg scheduling latency: {avg_scheduling_time*1000:.2f}ms, max: {max_scheduling_time*1000:.2f}ms")
        print(f"   Final queue size: {final_queue_size}")
    
    async def test_retry_backoff_scaling_performance(self):
        """Test performance of retry backoff calculation at scale."""
        backoff_test_webhooks = 1000
        max_attempt_count = 8  # Test up to 8 retry attempts
        
        # Schedule webhooks and simulate multiple retry attempts
        webhook_ids = []
        backoff_calculation_times = []
        
        for i in range(backoff_test_webhooks):
            webhook_id = f"backoff_scale_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Backoff scaling test"
            )
        
        # Test backoff calculation performance at various attempt counts
        attempt_performance = {}
        
        for attempt_count in range(1, max_attempt_count + 1):
            attempt_calculation_times = []
            
            # Measure backoff calculation time for this attempt count
            for _ in range(100):  # 100 calculations per attempt level
                calc_start = time.perf_counter()
                next_retry_time = self.retry_manager._calculate_next_retry_time(attempt_count)
                calc_end = time.perf_counter()
                
                calculation_time = calc_end - calc_start
                attempt_calculation_times.append(calculation_time)
                
                # Verify backoff time is reasonable
                assert next_retry_time is not None, f"Should calculate backoff for attempt {attempt_count}"
            
            avg_calc_time = statistics.mean(attempt_calculation_times)
            max_calc_time = max(attempt_calculation_times)
            
            attempt_performance[attempt_count] = {
                "avg_time": avg_calc_time,
                "max_time": max_calc_time,
                "samples": len(attempt_calculation_times)
            }
            
            backoff_calculation_times.extend(attempt_calculation_times)
        
        # Backoff scaling performance assertions
        overall_avg_time = statistics.mean(backoff_calculation_times)
        overall_max_time = max(backoff_calculation_times)
        
        # Backoff calculation should be fast even at high attempt counts
        assert overall_avg_time < 0.001, f"Average backoff calculation {overall_avg_time*1000:.3f}ms should be < 1ms"
        assert overall_max_time < 0.005, f"Max backoff calculation {overall_max_time*1000:.3f}ms should be < 5ms"
        
        # Performance should not degrade significantly with attempt count
        first_attempt_avg = attempt_performance[1]["avg_time"]
        last_attempt_avg = attempt_performance[max_attempt_count]["avg_time"]
        performance_degradation = last_attempt_avg / first_attempt_avg
        
        assert performance_degradation < 3.0, f"Performance degradation {performance_degradation:.1f}x should be < 3x"
        
        print(f"✅ Retry backoff scaling performance:")
        print(f"   {len(backoff_calculation_times)} total calculations across {max_attempt_count} attempt levels")
        print(f"   Overall avg: {overall_avg_time*1000:.3f}ms, max: {overall_max_time*1000:.3f}ms")
        print(f"   Performance degradation: {performance_degradation:.1f}x from attempt 1 to {max_attempt_count}")
        
        # Print performance breakdown by attempt count
        for attempt, perf in attempt_performance.items():
            print(f"   Attempt {attempt}: {perf['avg_time']*1000:.3f}ms avg, {perf['max_time']*1000:.3f}ms max")
    
    @pytest.mark.slow
    async def test_retry_queue_cleanup_performance(self):
        """Test performance of retry queue cleanup operations in production scenarios."""
        cleanup_test_size = 2000
        success_rate_for_completion = 0.9  # 90% of webhooks will eventually succeed
        
        # Phase 1: Build up large retry queue
        buildup_start = time.perf_counter()
        webhook_ids = []
        
        for i in range(cleanup_test_size):
            webhook_id = f"cleanup_{i}_{get_next_webhook_counter()}"
            webhook_ids.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Cleanup test"
            )
        
        buildup_duration = time.perf_counter() - buildup_start
        initial_queue_size = len(self.retry_manager._retry_queue)
        initial_records_count = len(self.retry_manager._retry_records)
        
        # Phase 2: Simulate successful completions and cleanup
        self.production_executor.success_rate = success_rate_for_completion
        
        # Set webhooks ready for processing in batches
        completed_webhooks = []
        cleanup_performance = []
        
        batch_size = 200
        for batch_start in range(0, len(webhook_ids), batch_size):
            batch_end = min(batch_start + batch_size, len(webhook_ids))
            batch_webhooks = webhook_ids[batch_start:batch_end]
            
            # Set batch ready for retry
            for webhook_id in batch_webhooks:
                retry_record = self.retry_manager._retry_records[webhook_id]
                retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Process batch and measure cleanup performance
            cleanup_start = time.perf_counter()
            batch_results = await self.retry_manager.process_retry_queue()
            
            # Simulate cleanup of completed webhooks
            newly_completed = []
            for webhook_id in batch_webhooks:
                retry_record = self.retry_manager._retry_records.get(webhook_id)
                if retry_record and retry_record.retry_status.value in ["success", "permanently_disabled"]:
                    newly_completed.append(webhook_id)
            
            # Remove completed webhooks (simulate production cleanup)
            for webhook_id in newly_completed:
                if webhook_id in self.retry_manager._retry_records:
                    del self.retry_manager._retry_records[webhook_id]
                if webhook_id in self.retry_manager._retry_queue:
                    self.retry_manager._retry_queue.remove(webhook_id)
            
            cleanup_end = time.perf_counter()
            batch_cleanup_duration = cleanup_end - cleanup_start
            
            completed_webhooks.extend(newly_completed)
            cleanup_performance.append({
                "batch_size": len(batch_webhooks),
                "processed": batch_results["processed"],
                "completed": len(newly_completed),
                "cleanup_duration": batch_cleanup_duration,
                "remaining_queue_size": len(self.retry_manager._retry_queue),
                "remaining_records": len(self.retry_manager._retry_records)
            })
        
        final_queue_size = len(self.retry_manager._retry_queue)
        final_records_count = len(self.retry_manager._retry_records)
        
        # Cleanup performance assertions
        total_cleanup_duration = sum(perf["cleanup_duration"] for perf in cleanup_performance)
        total_completed = len(completed_webhooks)
        
        # Should have completed significant portion of webhooks
        completion_rate = total_completed / cleanup_test_size
        assert completion_rate > 0.5, f"Completion rate {completion_rate:.1%} should be > 50%"
        
        # Cleanup should be efficient
        avg_cleanup_duration = total_cleanup_duration / len(cleanup_performance)
        cleanup_rate = total_completed / total_cleanup_duration if total_cleanup_duration > 0 else 0
        
        assert avg_cleanup_duration < 15.0, f"Average cleanup duration {avg_cleanup_duration:.2f}s should be < 15.0s"
        assert cleanup_rate > 2, f"Cleanup rate {cleanup_rate:.1f}/s should be > 2/s"
        
        # Queue size should decrease appropriately
        queue_reduction = initial_queue_size - final_queue_size
        assert queue_reduction >= total_completed * 0.8, "Queue reduction should reflect completed webhooks"
        
        print(f"✅ Retry queue cleanup performance:")
        print(f"   Initial queue: {initial_queue_size}, final: {final_queue_size} (reduced by {queue_reduction})")
        print(f"   Completed webhooks: {total_completed}/{cleanup_test_size} ({completion_rate:.1%})")
        print(f"   Cleanup rate: {cleanup_rate:.1f}/s, avg batch duration: {avg_cleanup_duration:.2f}s")
        print(f"   Records: {initial_records_count} → {final_records_count}")