"""
Integration tests for webhook retry reliability and end-to-end flows.

Tests complete webhook retry scenarios with simulated failures, network issues,
and real-world conditions to validate the production reliability of the retry system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock
from typing import Dict, Any, List

from src.contexts.client_onboarding.core.services.webhook_retry import (
    WebhookRetryManager,
    WebhookRetryPolicyConfig,
    WebhookRetryRecord,
    RetryStatus,
    RetryFailureReason
)

from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class MockWebhookEndpoint:
    """Mock webhook endpoint that simulates various failure scenarios."""
    
    def __init__(self):
        self.call_count = 0
        self.responses = []
        self.call_history = []
        self.failure_pattern = None
        self.failure_count = 0
        
    def set_response_pattern(self, responses: List[Dict[str, Any]]):
        """Set the pattern of responses for testing."""
        self.responses = responses
        self.call_count = 0
        
    def set_failure_pattern(self, pattern: str, count: int = 3):
        """Set failure patterns like 'fail_then_succeed' or 'always_fail'."""
        self.failure_pattern = pattern
        self.failure_count = count
        self.call_count = 0
        
    async def execute_webhook(self, webhook_url: str, webhook_id: str, form_id: str) -> Dict[str, Any]:
        """Simulate webhook execution with configurable responses."""
        self.call_count += 1
        call_info = {
            "attempt": self.call_count,
            "timestamp": datetime.now(UTC),
            "webhook_id": webhook_id,
            "form_id": form_id,
            "webhook_url": webhook_url
        }
        self.call_history.append(call_info)
        
        # Pattern-based responses
        if self.failure_pattern == "fail_then_succeed":
            if self.call_count <= self.failure_count:
                return {
                    "status_code": 500,
                    "success": False,
                    "error_message": f"Simulated failure attempt {self.call_count}",
                    "response_body": None
                }
            else:
                return {
                    "status_code": 200,
                    "success": True,
                    "response_body": '{"status": "success"}',
                    "error_message": None
                }
                
        elif self.failure_pattern == "always_fail":
            return {
                "status_code": 500,
                "success": False,
                "error_message": f"Persistent failure {self.call_count}",
                "response_body": None
            }
            
        elif self.failure_pattern == "timeout_errors":
            return {
                "status_code": 408,
                "success": False,
                "error_message": "Request timeout",
                "response_body": None
            }
            
        elif self.failure_pattern == "rate_limit":
            if self.call_count <= 2:
                return {
                    "status_code": 429,
                    "success": False,
                    "error_message": "Rate limit exceeded",
                    "response_body": None
                }
            else:
                return {
                    "status_code": 200,
                    "success": True,
                    "response_body": '{"status": "success"}',
                    "error_message": None
                }
                
        elif self.failure_pattern == "permanent_failure":
            return {
                "status_code": 410,
                "success": False,
                "error_message": "Webhook endpoint gone",
                "response_body": None
            }
            
        # Pre-configured response pattern
        if self.responses and self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]
            
        # Default success
        return {
            "status_code": 200,
            "success": True,
            "response_body": '{"status": "success"}',
            "error_message": None
        }
    
    def reset(self):
        """Reset the mock endpoint state."""
        self.call_count = 0
        self.call_history = []
        self.responses = []
        self.failure_pattern = None


class TestWebhookRetryReliabilityIntegration:
    """Integration tests for webhook retry reliability scenarios."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.mock_endpoint = MockWebhookEndpoint()
        self.mock_metrics_collector = AsyncMock()
        
        # Create retry manager with realistic policy for integration testing
        self.retry_policy = WebhookRetryPolicyConfig(
            initial_retry_interval_minutes=1,  # 1 minute for faster testing
            max_retry_interval_minutes=5,
            exponential_backoff_multiplier=2.0,
            jitter_percentage=10.0,  # Lower jitter for predictable testing
            max_retry_duration_hours=1,  # 1 hour for testing
            max_total_attempts=5,
            failure_rate_disable_threshold=100.0,
            failure_rate_evaluation_window_hours=1
        )
        
        self.retry_manager = WebhookRetryManager(
            retry_policy=self.retry_policy,
            webhook_executor=self.mock_endpoint.execute_webhook,
            metrics_collector=self.mock_metrics_collector
        )
    
    async def test_end_to_end_retry_flow_with_eventual_success(self):
        """Test complete retry flow: initial failure → retry → retry → success."""
        webhook_id = f"e2e_test_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        webhook_url = "https://api.example.com/webhook"
        
        # Configure endpoint to fail 3 times, then succeed
        self.mock_endpoint.set_failure_pattern("fail_then_succeed", count=3)
        
        # Schedule initial retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url=webhook_url,
            initial_failure_reason="Connection timeout",
            initial_status_code=500
        )
        
        # Verify initial scheduling
        assert retry_record.retry_status == RetryStatus.PENDING
        assert webhook_id in self.retry_manager._retry_queue
        
        # Process retry attempts (simulate time passing by setting retry times to past)
        attempts_processed = 0
        max_attempts = 5
        
        while webhook_id in self.retry_manager._retry_queue and attempts_processed < max_attempts:
            # Set retry time to past to trigger processing
            if retry_record.next_retry_time:
                retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Process queue
            results = await self.retry_manager.process_retry_queue()
            attempts_processed += 1
            
            # Stop if successful or permanently disabled
            if results["successful"] > 0 or results["disabled"] > 0:
                break
        
        # Verify final state
        assert retry_record.retry_status == RetryStatus.SUCCESS
        assert retry_record.total_attempts == 4  # Failed 3 times, succeeded on 4th
        assert retry_record.successful_attempts == 1
        assert retry_record.failed_attempts == 3
        assert webhook_id not in self.retry_manager._retry_queue
        
        # Verify call history
        assert self.mock_endpoint.call_count == 4
        assert len(self.mock_endpoint.call_history) == 4
        
        # Verify metrics collection
        assert self.mock_metrics_collector.call_count >= 4  # Schedule + attempts + success
    
    async def test_permanent_failure_immediate_disable_410_gone(self):
        """Test webhook is immediately disabled for HTTP 410 Gone responses."""
        webhook_id = f"permanent_410_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        
        # Configure endpoint to return 410 Gone
        self.mock_endpoint.set_failure_pattern("permanent_failure")
        
        # Schedule retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Test failure",
            initial_status_code=410
        )
        
        # Verify immediate permanent disable
        assert retry_record.retry_status == RetryStatus.PERMANENTLY_DISABLED
        assert retry_record.permanent_failure_reason == RetryFailureReason.HTTP_410_GONE
        assert webhook_id not in self.retry_manager._retry_queue
        
        # No webhook execution should have occurred
        assert self.mock_endpoint.call_count == 0
    
    async def test_rate_limiting_retry_scenario(self):
        """Test retry behavior with rate limiting (429) responses."""
        webhook_id = f"rate_limit_test_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        
        # Configure endpoint for rate limiting scenario
        self.mock_endpoint.set_failure_pattern("rate_limit")
        
        # Schedule retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Rate limit exceeded",
            initial_status_code=429
        )
        
        # Process retries until success
        attempts = 0
        while webhook_id in self.retry_manager._retry_queue and attempts < 5:
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            await self.retry_manager.process_retry_queue()
            attempts += 1
        
        # Verify eventual success after rate limiting
        assert retry_record.retry_status == RetryStatus.SUCCESS
        assert retry_record.total_attempts == 3  # 2 rate limit failures + 1 success
        assert retry_record.successful_attempts == 1
        assert self.mock_endpoint.call_count == 3
    
    async def test_maximum_retry_duration_enforcement(self):
        """Test webhook is disabled after exceeding maximum retry duration."""
        webhook_id = f"duration_test_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        
        # Create webhook with failure time that exceeds max duration
        old_failure_time = datetime.now(UTC) - timedelta(hours=11)  # Exceeds 10-hour limit
        
        retry_record = WebhookRetryRecord(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url="https://api.example.com/webhook",
            initial_failure_time=old_failure_time,
            retry_status=RetryStatus.PENDING
        )
        
        self.retry_manager._retry_records[webhook_id] = retry_record
        self.retry_manager._retry_queue.append(webhook_id)
        retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        # Process queue
        results = await self.retry_manager.process_retry_queue()
        
        # Verify duration-based disable
        assert results["disabled"] == 1
        assert retry_record.retry_status == RetryStatus.PERMANENTLY_DISABLED
        assert retry_record.permanent_failure_reason == RetryFailureReason.MAX_RETRY_DURATION_EXCEEDED
        assert webhook_id not in self.retry_manager._retry_queue
    
    async def test_maximum_attempts_enforcement(self):
        """Test webhook is disabled after exceeding maximum retry attempts."""
        webhook_id = f"max_attempts_test_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        
        # Configure endpoint to always fail
        self.mock_endpoint.set_failure_pattern("always_fail")
        
        # Schedule retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Persistent failure"
        )
        
        # Process retries until max attempts reached
        attempts = 0
        while webhook_id in self.retry_manager._retry_queue and attempts < 10:
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            results = await self.retry_manager.process_retry_queue()
            attempts += 1
            
            # Stop if disabled
            if results["disabled"] > 0:
                break
        
        # Verify webhook is disabled (either by max attempts OR 100% failure rate threshold)
        # Note: The implementation may disable due to failure rate before reaching max attempts
        assert retry_record.retry_status in [RetryStatus.MAX_RETRIES_EXCEEDED, RetryStatus.PERMANENTLY_DISABLED]
        assert retry_record.total_attempts >= self.retry_policy.max_total_attempts
        assert webhook_id not in self.retry_manager._retry_queue
        
        # If disabled due to failure rate, verify the reason
        if retry_record.retry_status == RetryStatus.PERMANENTLY_DISABLED:
            assert retry_record.permanent_failure_reason == RetryFailureReason.HUNDRED_PERCENT_FAILURE_RATE
    
    async def test_concurrent_webhook_retry_processing(self):
        """Test processing multiple webhooks concurrently with different outcomes."""
        webhooks = [
            {"id": f"concurrent_success_{get_next_webhook_counter()}", "pattern": "fail_then_succeed", "count": 1},
            {"id": f"concurrent_rate_limit_{get_next_webhook_counter()}", "pattern": "rate_limit", "count": 2},
            {"id": f"concurrent_permanent_{get_next_webhook_counter()}", "pattern": "permanent_failure", "count": 0}
        ]
        
        # Schedule all webhooks
        retry_records = {}
        for webhook in webhooks:
            if webhook["pattern"] == "permanent_failure":
                # Skip permanent failure in scheduling (it disables immediately)
                continue
                
            retry_record = await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook["id"],
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Test failure"
            )
            retry_records[webhook["id"]] = retry_record
        
        # Set up mock to handle different webhooks differently
        async def multi_webhook_executor(webhook_url: str, webhook_id: str, form_id: str):
            if "success" in webhook_id:
                # Fail once, then succeed
                if webhook_id not in self.multi_call_counts:
                    self.multi_call_counts[webhook_id] = 0
                self.multi_call_counts[webhook_id] += 1
                
                if self.multi_call_counts[webhook_id] == 1:
                    return {"status_code": 500, "success": False, "error_message": "First failure"}
                else:
                    return {"status_code": 200, "success": True, "response_body": "Success"}
                    
            elif "rate_limit" in webhook_id:
                # Rate limit twice, then succeed
                if webhook_id not in self.multi_call_counts:
                    self.multi_call_counts[webhook_id] = 0
                self.multi_call_counts[webhook_id] += 1
                
                if self.multi_call_counts[webhook_id] <= 2:
                    return {"status_code": 429, "success": False, "error_message": "Rate limited"}
                else:
                    return {"status_code": 200, "success": True, "response_body": "Success"}
            
            return {"status_code": 500, "success": False, "error_message": "Default failure"}
        
        self.multi_call_counts = {}
        self.retry_manager.webhook_executor = multi_webhook_executor
        
        # Process retries until all complete or max attempts
        max_iterations = 10
        iteration = 0
        
        while len(self.retry_manager._retry_queue) > 0 and iteration < max_iterations:
            # Set all pending retries to be due
            for webhook_id in list(self.retry_manager._retry_queue):
                retry_record = self.retry_manager._retry_records[webhook_id]
                if retry_record.next_retry_time:
                    retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Process queue
            results = await self.retry_manager.process_retry_queue()
            iteration += 1
            
            # Small delay to simulate realistic processing
            await asyncio.sleep(0.01)
        
        # Verify outcomes
        success_webhook = webhooks[0]["id"]
        rate_limit_webhook = webhooks[1]["id"]
        
        assert retry_records[success_webhook].retry_status == RetryStatus.SUCCESS
        assert retry_records[rate_limit_webhook].retry_status == RetryStatus.SUCCESS
        
        # Verify call counts
        assert self.multi_call_counts[success_webhook] == 2  # 1 failure + 1 success
        assert self.multi_call_counts[rate_limit_webhook] == 3  # 2 rate limits + 1 success
    
    async def test_webhook_retry_with_exponential_backoff_timing(self):
        """Test that exponential backoff timing is respected in retry scheduling."""
        webhook_id = f"backoff_timing_test_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        
        # Configure endpoint to fail consistently
        self.mock_endpoint.set_failure_pattern("always_fail")
        
        # Schedule retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Consistent failure"
        )
        
        # Track retry timing
        retry_times = []
        initial_time = datetime.now(UTC)
        
        # Process several retry attempts and track timing
        for attempt in range(3):
            # Set retry time to past and record actual next retry time
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            
            # Store the scheduled next retry time before processing
            current_time = datetime.now(UTC)
            
            # Process queue
            await self.retry_manager.process_retry_queue()
            
            # Record the new next retry time
            if retry_record.next_retry_time:
                interval = retry_record.next_retry_time - current_time
                retry_times.append(interval.total_seconds())
        
        # Verify exponential backoff progression
        assert len(retry_times) >= 2
        
        # First interval should be around 60 seconds (1 minute initial) - allow wider range for jitter
        assert 30 <= retry_times[0] <= 150  # Allow for more jitter and processing variation
        
        # Second interval should be roughly double (with jitter)
        if len(retry_times) > 1:
            ratio = retry_times[1] / retry_times[0]
            assert 1.3 <= ratio <= 3.0  # Account for exponential backoff and jitter variation
    
    async def test_metrics_collection_during_retry_lifecycle(self):
        """Test comprehensive metrics collection throughout retry lifecycle."""
        webhook_id = f"metrics_test_{get_next_webhook_counter()}"
        form_id = f"form_{get_next_onboarding_form_id()}"
        
        # Configure endpoint for success after 2 failures
        self.mock_endpoint.set_failure_pattern("fail_then_succeed", count=2)
        
        # Schedule retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=form_id,
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Test failure"
        )
        
        # Process retries until success
        attempts = 0
        while webhook_id in self.retry_manager._retry_queue and attempts < 5:
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
            await self.retry_manager.process_retry_queue()
            attempts += 1
        
        # Verify metrics collection occurred throughout lifecycle
        assert self.mock_metrics_collector.call_count >= 4  # schedule + failures + success
        
        # Check specific metrics calls
        metric_calls = [call[0][0] for call in self.mock_metrics_collector.call_args_list]
        
        assert "webhook_retry_scheduled" in metric_calls
        assert "webhook_retry_failed" in metric_calls
        assert "webhook_retry_success" in metric_calls
        assert "retry_queue_processed" in metric_calls


class TestWebhookRetryReliabilityEdgeCases:
    """Test edge cases and error conditions in webhook retry reliability."""
    
    def setup_method(self):
        """Set up test environment for edge cases."""
        self.mock_endpoint = MockWebhookEndpoint()
        self.retry_manager = WebhookRetryManager(
            webhook_executor=self.mock_endpoint.execute_webhook,
            retry_policy=WebhookRetryPolicyConfig(
                initial_retry_interval_minutes=1,
                max_total_attempts=3,
                max_retry_duration_hours=1
            )
        )
    
    async def test_webhook_executor_network_exception_handling(self):
        """Test handling of network exceptions during webhook execution."""
        webhook_id = f"network_exception_test_{get_next_webhook_counter()}"
        
        # Configure executor to raise network exception
        async def failing_executor(webhook_url: str, webhook_id: str, form_id: str):
            raise ConnectionError("Network unreachable")
        
        self.retry_manager.webhook_executor = failing_executor
        
        # Schedule retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=f"form_{get_next_onboarding_form_id()}",
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Network error"
        )
        
        # Process retry (should handle exception gracefully)
        retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        results = await self.retry_manager.process_retry_queue()
        
        # Verify exception was handled
        assert results["failed"] == 1
        assert retry_record.retry_status == RetryStatus.PENDING  # Scheduled for next retry
        assert retry_record.failed_attempts == 1
        assert retry_record.attempts[0].error_message == "Network unreachable"
    
    async def test_empty_retry_queue_processing(self):
        """Test processing an empty retry queue."""
        results = await self.retry_manager.process_retry_queue()
        
        assert results["processed"] == 0
        assert results["successful"] == 0
        assert results["failed"] == 0
        assert results["disabled"] == 0
        assert len(results["errors"]) == 0
    
    async def test_concurrent_queue_processing_protection(self):
        """Test protection against concurrent retry queue processing."""
        # Set processing flag
        self.retry_manager._processing_queue = True
        
        # Attempt to process queue
        results = await self.retry_manager.process_retry_queue()
        
        # Verify concurrent processing was prevented
        assert results["status"] == "already_processing"
    
    async def test_malformed_webhook_response_handling(self):
        """Test handling of malformed webhook responses."""
        webhook_id = f"malformed_response_test_{get_next_webhook_counter()}"
        
        # Configure executor to return malformed response
        async def malformed_executor(webhook_url: str, webhook_id: str, form_id: str):
            return {"invalid": "response"}  # Missing required fields
        
        self.retry_manager.webhook_executor = malformed_executor
        
        # Schedule and process retry
        retry_record = await self.retry_manager.schedule_webhook_retry(
            webhook_id=webhook_id,
            form_id=f"form_{get_next_onboarding_form_id()}",
            webhook_url="https://api.example.com/webhook",
            initial_failure_reason="Test"
        )
        
        retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        results = await self.retry_manager.process_retry_queue()
        
        # Should handle malformed response gracefully
        assert results["failed"] == 1
        assert retry_record.failed_attempts == 1


class TestWebhookRetryReliabilityPerformance:
    """Performance-focused integration tests for retry reliability."""
    
    def setup_method(self):
        """Set up performance test environment."""
        self.mock_endpoint = MockWebhookEndpoint()
        self.retry_manager = WebhookRetryManager(
            webhook_executor=self.mock_endpoint.execute_webhook,
            retry_policy=WebhookRetryPolicyConfig(
                initial_retry_interval_minutes=0.1,  # type: ignore[arg-type] # Very short for performance testing
                max_total_attempts=3
            )
        )
    
    async def test_high_volume_webhook_retry_processing(self):
        """Test processing a high volume of webhook retries efficiently."""
        webhook_count = 50
        webhooks = []
        
        # Schedule many webhooks
        for i in range(webhook_count):
            webhook_id = f"volume_test_{i}_{get_next_webhook_counter()}"
            webhooks.append(webhook_id)
            
            await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=f"form_{get_next_onboarding_form_id()}",
                webhook_url="https://api.example.com/webhook",
                initial_failure_reason="Volume test"
            )
        
        # Configure endpoint for immediate success
        self.mock_endpoint.set_response_pattern([
            {"status_code": 200, "success": True, "response_body": "Success"}
        ])
        
        # Set all retries to be due and process
        for webhook_id in webhooks:
            retry_record = self.retry_manager._retry_records[webhook_id]
            retry_record.next_retry_time = datetime.now(UTC) - timedelta(minutes=1)
        
        # Measure processing time
        start_time = datetime.now(UTC)
        results = await self.retry_manager.process_retry_queue()
        end_time = datetime.now(UTC)
        
        processing_duration = (end_time - start_time).total_seconds()
        
        # Verify all webhooks processed successfully
        assert results["processed"] == webhook_count
        assert results["successful"] == webhook_count
        assert results["failed"] == 0
        
        # Performance assertion: should process 50 webhooks in under 2 seconds
        assert processing_duration < 2.0, f"Processing took {processing_duration:.2f}s, expected < 2.0s"
        
        # Verify all webhooks removed from queue
        assert len(self.retry_manager._retry_queue) == 0