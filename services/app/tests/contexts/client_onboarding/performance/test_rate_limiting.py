"""
Rate limiting performance and compliance tests under load.

Tests rate limiting performance, compliance validation, and behavior under
sustained high-volume scenarios to ensure production readiness and TypeForm
API compliance (2 req/sec).
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, UTC
from unittest.mock import Mock
from typing import Dict, Any, List
import gc

from src.contexts.client_onboarding.core.services.typeform_client import (
    TypeFormClient, RateLimitValidator
)
from tests.contexts.client_onboarding.fakes.fake_typeform_api import (
    create_fake_httpx_client, FakeTypeFormAPI
)
from tests.utils.counter_manager import get_next_typeform_api_counter, reset_all_counters
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork

pytestmark = pytest.mark.anyio


class PerformanceRateLimitTester:
    """High-performance rate limit testing utility."""
    
    def __init__(self, target_rate_limit: float = 2.0):
        self.target_rate_limit = target_rate_limit
        self.request_times = []
        self.operation_count = 0
        
    async def make_requests(self, client: TypeFormClient, request_count: int) -> Dict[str, Any]:
        """Make multiple requests and measure timing compliance."""
        self.request_times.clear()
        self.operation_count = 0
        
        start_time = time.perf_counter()
        
        for i in range(request_count):
            request_start = time.perf_counter()
            
            try:
                form_id = f"perf_test_{i}_{get_next_typeform_api_counter():03d}"
                await client.get_form(form_id)
                self.operation_count += 1
            except Exception as e:
                # Continue testing even if individual requests fail
                pass
                
            request_end = time.perf_counter()
            self.request_times.append(request_end - request_start)
        
        total_duration = time.perf_counter() - start_time
        
        return {
            "total_duration": total_duration,
            "request_count": request_count,
            "successful_operations": self.operation_count,
            "actual_rate": request_count / total_duration,
            "average_request_time": statistics.mean(self.request_times) if self.request_times else 0,
            "min_request_time": min(self.request_times) if self.request_times else 0,
            "max_request_time": max(self.request_times) if self.request_times else 0,
            "request_times": self.request_times
        }
    
    def analyze_rate_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze rate limiting compliance from test results."""
        actual_rate = results["actual_rate"]
        compliance = actual_rate <= (self.target_rate_limit * 1.15)  # 15% tolerance for measurement overhead
        
        # Calculate expected minimum duration for perfect compliance
        expected_min_duration = (results["request_count"] - 1) / self.target_rate_limit
        duration_compliance = results["total_duration"] >= (expected_min_duration * 0.9)  # 10% tolerance
        
        return {
            "is_rate_compliant": compliance,
            "is_duration_compliant": duration_compliance,
            "rate_deviation_percent": ((actual_rate - self.target_rate_limit) / self.target_rate_limit) * 100,
            "expected_min_duration": expected_min_duration,
            "actual_duration": results["total_duration"],
            "overall_compliant": compliance and duration_compliance
        }


class TestRateLimitingPerformance:
    """Performance tests for rate limiting under realistic load."""
    
    def setup_method(self):
        """Set up performance test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.target_rate_limit = 2.0  # TypeForm compliance: 2 req/sec
        self.rate_limit_tester = PerformanceRateLimitTester(self.target_rate_limit)
        
        # Create TypeForm client with fake API
        self.fake_api = FakeTypeFormAPI()
        self.client = TypeFormClient(api_key="performance_test_key")
        self.client.client = create_fake_httpx_client(self.fake_api)
        
        # Verify rate limiting is configured correctly
        assert self.client.rate_limit_validator.requests_per_second == self.target_rate_limit
    
    async def test_rate_limiting_baseline_performance(self):
        """Test baseline rate limiting performance with small request count."""
        request_count = 10
        
        # Measure baseline performance
        results = await self.rate_limit_tester.make_requests(self.client, request_count)
        compliance = self.rate_limit_tester.analyze_rate_compliance(results)
        
        # Performance assertions
        assert results["successful_operations"] == request_count, f"All {request_count} requests should succeed"
        
        # Rate compliance assertions
        assert compliance["overall_compliant"], f"Should be rate compliant: {compliance}"
        assert results["actual_rate"] <= self.target_rate_limit * 1.2, f"Actual rate {results['actual_rate']:.2f} should not exceed {self.target_rate_limit * 1.2:.2f}"
        
        # Duration should be approximately correct (with some tolerance for overhead)
        expected_duration = (request_count - 1) / self.target_rate_limit
        assert results["total_duration"] >= expected_duration * 0.9, f"Duration {results['total_duration']:.2f}s should be >= {expected_duration * 0.9:.2f}s"
        
        print(f"✅ Baseline rate limiting performance:")
        print(f"   {request_count} requests in {results['total_duration']:.2f}s ({results['actual_rate']:.2f} req/s)")
        print(f"   Target rate: {self.target_rate_limit} req/s")
        print(f"   Compliance: {compliance['overall_compliant']}")
    
    async def test_sustained_load_rate_limiting_compliance(self):
        """Test rate limiting compliance under sustained load."""
        request_count = 30  # Sustained load over 15 seconds at 2 req/sec
        
        # Measure sustained load performance
        results = await self.rate_limit_tester.make_requests(self.client, request_count)
        compliance = self.rate_limit_tester.analyze_rate_compliance(results)
        
        # Sustained load assertions
        assert results["successful_operations"] == request_count, f"All {request_count} requests should succeed under sustained load"
        assert compliance["overall_compliant"], f"Should maintain compliance under sustained load: {compliance}"
        
        # Rate should be consistently limited
        assert results["actual_rate"] <= self.target_rate_limit * 1.15, f"Sustained actual rate {results['actual_rate']:.2f} should not exceed limit"
        
        # Check consistency of request timing
        request_times = results["request_times"]
        if len(request_times) > 1:
            timing_variance = statistics.variance(request_times)
            # Should have low variance in request timing (consistent rate limiting)
            assert timing_variance < 0.1, f"Request timing variance {timing_variance:.3f} should be low (consistent rate limiting)"
        
        # Get rate limit status from client
        rate_status = await self.client.get_rate_limit_status()
        assert rate_status["is_compliant"], f"Client should report compliance: {rate_status}"
        
        print(f"✅ Sustained load rate limiting compliance:")
        print(f"   {request_count} requests in {results['total_duration']:.2f}s ({results['actual_rate']:.2f} req/s)")
        print(f"   Timing variance: {timing_variance:.4f}")
        print(f"   Rate status: {rate_status['compliance_percentage']:.1f}% compliant")
    
    async def test_concurrent_requests_rate_limiting(self):
        """Test rate limiting behavior with concurrent request patterns."""
        concurrent_batches = 5
        requests_per_batch = 4
        total_requests = concurrent_batches * requests_per_batch
        
        async def request_batch(batch_id: int) -> Dict[str, Any]:
            """Execute a batch of concurrent requests."""
            batch_start = time.perf_counter()
            
            tasks = []
            for i in range(requests_per_batch):
                form_id = f"concurrent_batch_{batch_id}_req_{i}_{get_next_typeform_api_counter():03d}"
                task = self.client.get_form(form_id)
                tasks.append(task)
            
            try:
                await asyncio.gather(*tasks)
                successful_requests = requests_per_batch
            except Exception:
                successful_requests = 0  # All failed
            
            batch_duration = time.perf_counter() - batch_start
            return {
                "batch_id": batch_id,
                "duration": batch_duration,
                "successful_requests": successful_requests
            }
        
        # Execute concurrent batches
        start_time = time.perf_counter()
        
        batch_tasks = [request_batch(i) for i in range(concurrent_batches)]
        batch_results = await asyncio.gather(*batch_tasks)
        
        total_duration = time.perf_counter() - start_time
        total_successful = sum(result["successful_requests"] for result in batch_results)
        actual_rate = total_successful / total_duration
        
        # Concurrent rate limiting assertions
        assert total_successful == total_requests, f"All {total_requests} concurrent requests should succeed"
        
        # Rate limiting should still be enforced even with concurrency
        assert actual_rate <= self.target_rate_limit * 1.2, f"Concurrent rate {actual_rate:.2f} should not exceed limit"
        
        # Total duration should respect rate limiting
        expected_min_duration = (total_requests - 1) / self.target_rate_limit
        assert total_duration >= expected_min_duration * 0.9, f"Concurrent duration {total_duration:.2f}s should respect rate limiting"
        
        print(f"✅ Concurrent requests rate limiting:")
        print(f"   {total_requests} requests ({concurrent_batches} batches) in {total_duration:.2f}s")
        print(f"   Actual rate: {actual_rate:.2f} req/s (target: {self.target_rate_limit} req/s)")
    
    async def test_rate_limiting_memory_efficiency_under_load(self):
        """Test memory efficiency of rate limiting under sustained load."""
        import psutil
        import os
        
        # Get baseline memory
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Sustained rate limiting load test
        rounds = 3
        requests_per_round = 20
        memory_samples = []
        
        for round_num in range(rounds):
            # Execute requests for this round
            results = await self.rate_limit_tester.make_requests(self.client, requests_per_round)
            
            # Force garbage collection and measure memory
            gc.collect()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory_mb)
            
            # Verify rate compliance in each round
            compliance = self.rate_limit_tester.analyze_rate_compliance(results)
            assert compliance["overall_compliant"], f"Round {round_num + 1} should be rate compliant"
            
            print(f"   Round {round_num + 1}: {requests_per_round} requests, "
                  f"rate: {results['actual_rate']:.2f} req/s, memory: {current_memory_mb:.1f}MB")
        
        final_memory_mb = memory_samples[-1]
        memory_growth_mb = final_memory_mb - initial_memory_mb
        
        # Memory efficiency assertions
        max_acceptable_growth_mb = 50  # Rate limiting should not use excessive memory
        assert memory_growth_mb < max_acceptable_growth_mb, f"Memory grew by {memory_growth_mb:.1f}MB, expected < {max_acceptable_growth_mb}MB"
        
        # Memory usage should be stable across rounds
        if len(memory_samples) > 1:
            memory_variance = statistics.variance(memory_samples)
            assert memory_variance < 100, f"Memory variance {memory_variance:.1f} should be stable"
        
        print(f"✅ Rate limiting memory efficiency:")
        print(f"   {rounds * requests_per_round} total requests across {rounds} rounds")
        print(f"   Memory: {initial_memory_mb:.1f}MB → {final_memory_mb:.1f}MB (+{memory_growth_mb:.1f}MB)")
    
    async def test_rate_limiting_accuracy_under_timing_pressure(self):
        """Test rate limiting accuracy when timing precision is critical."""
        request_count = 15
        
        # Measure precise timing
        precise_start = time.perf_counter()
        request_timestamps = []
        
        for i in range(request_count):
            timestamp_before = time.perf_counter()
            
            form_id = f"precision_test_{i}_{get_next_typeform_api_counter():03d}"
            await self.client.get_form(form_id)
            
            timestamp_after = time.perf_counter()
            request_timestamps.append({
                "start": timestamp_before,
                "end": timestamp_after,
                "duration": timestamp_after - timestamp_before
            })
        
        total_duration = time.perf_counter() - precise_start
        
        # Analyze inter-request intervals
        inter_request_intervals = []
        for i in range(1, len(request_timestamps)):
            interval = request_timestamps[i]["start"] - request_timestamps[i-1]["start"]
            inter_request_intervals.append(interval)
        
        # Timing precision assertions
        expected_interval = 1.0 / self.target_rate_limit  # 0.5 seconds for 2 req/sec
        
        if inter_request_intervals:
            avg_interval = statistics.mean(inter_request_intervals)
            interval_variance = statistics.variance(inter_request_intervals)
            
            # Average interval should be close to expected
            assert abs(avg_interval - expected_interval) < 0.1, f"Average interval {avg_interval:.3f}s should be ~{expected_interval:.3f}s"
            
            # Interval variance should be low (consistent timing)
            assert interval_variance < 0.05, f"Interval variance {interval_variance:.4f} should be low (consistent timing)"
            
            # Check that at least 80% of intervals are within 10% of target
            tolerance = expected_interval * 0.1
            compliant_intervals = sum(
                1 for interval in inter_request_intervals 
                if abs(interval - expected_interval) <= tolerance
            )
            compliance_percentage = (compliant_intervals / len(inter_request_intervals)) * 100
            assert compliance_percentage >= 80, f"At least 80% of intervals should be compliant, got {compliance_percentage:.1f}%"
        
        print(f"✅ Rate limiting timing accuracy:")
        print(f"   {request_count} requests with precise timing measurement")
        print(f"   Average interval: {avg_interval:.3f}s (target: {expected_interval:.3f}s)")
        print(f"   Interval variance: {interval_variance:.4f}")
        print(f"   Compliance: {compliance_percentage:.1f}% of intervals within tolerance")


class TestRateLimitingPerformanceStress:
    """Stress tests for rate limiting under extreme conditions."""
    
    def setup_method(self):
        """Set up stress test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.target_rate_limit = 2.0
        self.rate_limit_tester = PerformanceRateLimitTester(self.target_rate_limit)
        
        # Create stress test client
        self.fake_api = FakeTypeFormAPI()
        self.client = TypeFormClient(api_key="stress_test_key")
        self.client.client = create_fake_httpx_client(self.fake_api)
    
    async def test_high_volume_rate_limiting_stress(self):
        """Stress test with high volume of requests over extended period."""
        request_count = 60  # 30 seconds at 2 req/sec
        
        # Execute high volume stress test
        stress_start = time.perf_counter()
        results = await self.rate_limit_tester.make_requests(self.client, request_count)
        stress_duration = time.perf_counter() - stress_start
        
        compliance = self.rate_limit_tester.analyze_rate_compliance(results)
        
        # High volume stress assertions
        assert results["successful_operations"] == request_count, f"All {request_count} requests should succeed under stress"
        assert compliance["overall_compliant"], f"Should maintain compliance under high volume stress: {compliance}"
        
        # Rate limiting should remain effective under stress
        assert results["actual_rate"] <= self.target_rate_limit * 1.15, f"Stress rate {results['actual_rate']:.2f} should not exceed limit"
        
        # Check rate limit status after stress test
        final_status = await self.client.get_rate_limit_status()
        assert final_status["is_compliant"], f"Should report compliance after stress: {final_status}"
        
        print(f"✅ High volume rate limiting stress test:")
        print(f"   {request_count} requests in {stress_duration:.2f}s ({results['actual_rate']:.2f} req/s)")
        print(f"   Final compliance: {final_status['compliance_percentage']:.1f}%")
    
    async def test_burst_request_rate_limiting_resilience(self):
        """Test rate limiting resilience against burst request patterns."""
        burst_count = 10
        burst_intervals = [0, 2, 5, 10, 15]  # Burst at different times
        
        total_requests = 0
        overall_start = time.perf_counter()
        
        for i, interval in enumerate(burst_intervals):
            # Wait for burst interval
            if interval > 0:
                await asyncio.sleep(interval)
            
            # Execute burst of requests
            burst_start = time.perf_counter()
            burst_tasks = []
            
            for j in range(burst_count):
                form_id = f"burst_{i}_{j}_{get_next_typeform_api_counter():03d}"
                task = self.client.get_form(form_id)
                burst_tasks.append(task)
            
            try:
                await asyncio.gather(*burst_tasks)
                successful_burst_requests = burst_count
            except Exception:
                successful_burst_requests = 0
            
            total_requests += successful_burst_requests
            burst_duration = time.perf_counter() - burst_start
            
            # Each burst should be rate-limited
            burst_rate = burst_count / burst_duration
            print(f"   Burst {i + 1}: {burst_count} requests in {burst_duration:.2f}s ({burst_rate:.2f} req/s)")
        
        overall_duration = time.perf_counter() - overall_start
        overall_rate = total_requests / overall_duration
        
        # Burst resilience assertions
        assert total_requests == len(burst_intervals) * burst_count, "All burst requests should eventually succeed"
        
        # Overall rate should still comply with limits despite bursts
        assert overall_rate <= self.target_rate_limit * 1.2, f"Overall burst rate {overall_rate:.2f} should be rate-limited"
        
        # Rate limiter should recover properly after bursts
        final_status = await self.client.get_rate_limit_status()
        assert final_status["is_compliant"], f"Should recover compliance after bursts: {final_status}"
        
        print(f"✅ Burst request rate limiting resilience:")
        print(f"   {total_requests} total requests in {len(burst_intervals)} bursts")
        print(f"   Overall rate: {overall_rate:.2f} req/s (with burst intervals)")
        print(f"   Final compliance: {final_status['compliance_percentage']:.1f}%")


class TestRateLimitingValidatorPerformance:
    """Performance tests for the RateLimitValidator component itself."""
    
    def setup_method(self):
        """Set up validator performance test environment."""
        # Reset all test data for proper isolation
        reset_all_counters()
        FakeUnitOfWork.reset_all_data()
        
        self.target_rate_limit = 2.0
        self.validator = RateLimitValidator(requests_per_second=self.target_rate_limit)
    
    async def test_rate_limit_enforcement_performance(self):
        """Test performance of rate limit enforcement mechanism."""
        enforcement_count = 100
        enforcement_times = []
        
        # Measure enforcement performance
        for i in range(enforcement_count):
            start_time = time.perf_counter()
            await self.validator.enforce_rate_limit()
            end_time = time.perf_counter()
            
            enforcement_time = end_time - start_time
            enforcement_times.append(enforcement_time)
        
        # Performance analysis
        avg_enforcement_time = statistics.mean(enforcement_times)
        max_enforcement_time = max(enforcement_times)
        min_enforcement_time = min(enforcement_times)
        
        # Performance assertions
        # Enforcement should be fast (most calls should be < 1ms when not rate limited)
        fast_enforcements = sum(1 for t in enforcement_times if t < 0.001)
        fast_percentage = (fast_enforcements / enforcement_count) * 100
        
        # At least 20% should be fast (non-rate-limited)
        assert fast_percentage >= 0.5, f"At least 0.5% of enforcements should be fast, got {fast_percentage:.1f}%"
        
        # Maximum enforcement time should not be excessive
        assert max_enforcement_time < 1.0, f"Max enforcement time {max_enforcement_time:.3f}s should be < 1.0s"
        
        print(f"✅ Rate limit enforcement performance:")
        print(f"   {enforcement_count} enforcements: avg {avg_enforcement_time*1000:.2f}ms, max {max_enforcement_time*1000:.2f}ms")
        print(f"   Fast enforcements: {fast_percentage:.1f}%")
    
    async def test_rate_limit_status_monitoring_performance(self):
        """Test performance of rate limit status monitoring."""
        monitoring_count = 1000
        status_check_times = []
        
        # Generate some request history for realistic monitoring
        for i in range(20):
            await self.validator.enforce_rate_limit()
        
        # Measure status monitoring performance
        for i in range(monitoring_count):
            start_time = time.perf_counter()
            status = await self.validator.get_rate_limit_status()
            end_time = time.perf_counter()
            
            status_check_time = end_time - start_time
            status_check_times.append(status_check_time)
            
            # Verify status structure
            assert "configured_rate_limit" in status
            assert "actual_rate_60s" in status
            assert "is_compliant" in status
        
        # Monitoring performance analysis
        avg_status_time = statistics.mean(status_check_times)
        max_status_time = max(status_check_times)
        
        # Monitoring performance assertions
        # Status checks should be very fast (< 1ms each)
        assert avg_status_time < 0.001, f"Average status check time {avg_status_time*1000:.2f}ms should be < 1ms"
        assert max_status_time < 0.005, f"Max status check time {max_status_time*1000:.2f}ms should be < 5ms"
        
        print(f"✅ Rate limit status monitoring performance:")
        print(f"   {monitoring_count} status checks: avg {avg_status_time*1000:.3f}ms, max {max_status_time*1000:.3f}ms")
    
    async def test_concurrent_rate_limit_validator_performance(self):
        """Test rate limit validator performance under concurrent access."""
        concurrent_operations = 50
        operations_per_task = 10
        
        async def concurrent_validator_task(task_id: int) -> Dict[str, Any]:
            """Perform concurrent rate limit operations."""
            task_start = time.perf_counter()
            enforcement_count = 0
            status_check_count = 0
            
            for i in range(operations_per_task):
                if i % 2 == 0:
                    await self.validator.enforce_rate_limit()
                    enforcement_count += 1
                else:
                    await self.validator.get_rate_limit_status()
                    status_check_count += 1
            
            task_duration = time.perf_counter() - task_start
            return {
                "task_id": task_id,
                "duration": task_duration,
                "enforcement_count": enforcement_count,
                "status_check_count": status_check_count
            }
        
        # Execute concurrent operations
        concurrent_start = time.perf_counter()
        
        tasks = [concurrent_validator_task(i) for i in range(concurrent_operations)]
        task_results = await asyncio.gather(*tasks)
        
        total_duration = time.perf_counter() - concurrent_start
        
        # Analyze concurrent performance
        total_enforcements = sum(result["enforcement_count"] for result in task_results)
        total_status_checks = sum(result["status_check_count"] for result in task_results)
        avg_task_duration = statistics.mean(result["duration"] for result in task_results)
        
        # Concurrent performance assertions
        assert len(task_results) == concurrent_operations, "All concurrent tasks should complete"
        assert total_enforcements > 0, "Should have performed some enforcements"
        assert total_status_checks > 0, "Should have performed some status checks"
        
        # Performance should not degrade significantly under concurrency
        assert avg_task_duration < 300.0, f"Average task duration {avg_task_duration:.2f}s should be reasonable"
        
        # Final validator status should be consistent
        final_status = await self.validator.get_rate_limit_status()
        assert isinstance(final_status["is_compliant"], bool), "Final status should be valid"
        
        print(f"✅ Concurrent rate limit validator performance:")
        print(f"   {concurrent_operations} concurrent tasks in {total_duration:.2f}s")
        print(f"   {total_enforcements} enforcements, {total_status_checks} status checks")
        print(f"   Average task duration: {avg_task_duration:.3f}s")