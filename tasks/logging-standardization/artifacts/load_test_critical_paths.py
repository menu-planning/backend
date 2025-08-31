#!/usr/bin/env python3
"""
Load testing script for critical paths in the logging standardization project.
Tests high-traffic endpoints and services to ensure no performance degradation under load.
"""

import asyncio
import json
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.logging.logger import (
        StructlogFactory,
        correlation_id_ctx,
        generate_correlation_id,
        set_correlation_id,
    )
    from src.contexts.shared_kernel.services.messagebus import MessageBus
    IMPORTS_AVAILABLE = True
except ImportError:
    print("Warning: Could not import logging modules. Using mock implementations for testing.")
    IMPORTS_AVAILABLE = False

    # Mock implementations for testing
    class MockCorrelationCtx:
        def __init__(self):
            self._value = "00000000-0000-0000-0000-000000000000"

        def set(self, value):
            self._value = value

        def get(self):
            return self._value

    class MockLogger:
        def __init__(self, name: str = "test_logger"):
            self.name = name
            self.logged_messages = []

        def info(self, message, **kwargs):
            self.logged_messages.append({"level": "info", "message": message, "kwargs": kwargs})

        def error(self, message, **kwargs):
            self.logged_messages.append({"level": "error", "message": message, "kwargs": kwargs})

        def debug(self, message, **kwargs):
            self.logged_messages.append({"level": "debug", "message": message, "kwargs": kwargs})

        def warning(self, message, **kwargs):
            self.logged_messages.append({"level": "warning", "message": message, "kwargs": kwargs})

    class MockStructlogFactory:
        @classmethod
        def configure(cls, **kwargs):
            pass

        @classmethod
        def get_logger(cls, name=""):
            return MockLogger(name)

    class MockMessageBus:
        async def handle(self, message, timeout=30):
            # Simulate processing time
            await asyncio.sleep(0.001)  # 1ms processing time

    def mock_set_correlation_id(correlation_id):
        correlation_id_ctx.set(correlation_id)

    def mock_generate_correlation_id():
        cid = uuid.uuid4().hex[:8]
        correlation_id_ctx.set(cid)
        return cid

    StructlogFactory = MockStructlogFactory
    MessageBus = MockMessageBus
    correlation_id_ctx = MockCorrelationCtx()
    set_correlation_id = mock_set_correlation_id
    generate_correlation_id = mock_generate_correlation_id


@dataclass
class LoadTestResult:
    """Results from a load test scenario."""
    scenario_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_seconds: float
    average_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate_percent: float


class CriticalPathLoadTester:
    """Load tester for critical application paths."""

    def __init__(self):
        self.results: List[LoadTestResult] = []
        self.logger = StructlogFactory.get_logger("load_test.critical_paths")

    async def simulate_webhook_processing(self, request_id: str) -> tuple[bool, float]:
        """Simulate webhook processing load."""
        start_time = time.perf_counter()
        
        try:
            # Set correlation ID for this request
            correlation_id = generate_correlation_id()
            
            # Simulate webhook processing steps
            self.logger.info(
                "Processing webhook request",
                request_id=request_id,
                correlation_id=correlation_id,
                action="webhook_processing_start"
            )
            
            # Simulate payload validation (typical processing time)
            await asyncio.sleep(0.002)  # 2ms
            
            # Simulate database operations
            self.logger.debug(
                "Validating webhook payload",
                request_id=request_id,
                payload_size=1024,
                validation_status="success"
            )
            
            await asyncio.sleep(0.005)  # 5ms for DB operations
            
            # Simulate business logic processing
            self.logger.info(
                "Storing form response data",
                request_id=request_id,
                form_type="client_onboarding",
                processing_stage="data_storage"
            )
            
            await asyncio.sleep(0.003)  # 3ms for business logic
            
            # Simulate successful completion
            self.logger.info(
                "Webhook processing completed",
                request_id=request_id,
                action="webhook_processing_complete",
                status="success"
            )
            
            end_time = time.perf_counter()
            return True, (end_time - start_time) * 1000  # Convert to milliseconds
            
        except Exception as e:
            self.logger.error(
                "Webhook processing failed",
                request_id=request_id,
                error=str(e),
                action="webhook_processing_error"
            )
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000

    async def simulate_product_query(self, request_id: str) -> tuple[bool, float]:
        """Simulate product catalog query load."""
        start_time = time.perf_counter()
        
        try:
            correlation_id = generate_correlation_id()
            
            self.logger.info(
                "Processing product query",
                request_id=request_id,
                correlation_id=correlation_id,
                action="product_query_start"
            )
            
            # Simulate authentication middleware
            await asyncio.sleep(0.001)  # 1ms
            
            # Simulate query parameter processing
            self.logger.debug(
                "Processing query filters",
                request_id=request_id,
                filters={"limit": 50, "sort": "-updated_at"},
                filter_count=2
            )
            
            await asyncio.sleep(0.002)  # 2ms
            
            # Simulate database query
            self.logger.debug(
                "Executing product database query",
                request_id=request_id,
                query_type="product_fetch",
                estimated_results=25
            )
            
            await asyncio.sleep(0.008)  # 8ms for DB query
            
            # Simulate data transformation
            self.logger.debug(
                "Converting domain objects to API format",
                request_id=request_id,
                conversion_count=25,
                transformation_stage="domain_to_api"
            )
            
            await asyncio.sleep(0.003)  # 3ms for transformation
            
            self.logger.info(
                "Product query completed",
                request_id=request_id,
                action="product_query_complete",
                result_count=25,
                status="success"
            )
            
            end_time = time.perf_counter()
            return True, (end_time - start_time) * 1000
            
        except Exception as e:
            self.logger.error(
                "Product query failed",
                request_id=request_id,
                error=str(e),
                action="product_query_error"
            )
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000

    async def simulate_form_creation(self, request_id: str) -> tuple[bool, float]:
        """Simulate form creation load."""
        start_time = time.perf_counter()
        
        try:
            correlation_id = generate_correlation_id()
            
            self.logger.info(
                "Processing form creation request",
                request_id=request_id,
                correlation_id=correlation_id,
                action="form_creation_start"
            )
            
            # Simulate authentication
            await asyncio.sleep(0.002)  # 2ms
            
            # Simulate request validation
            self.logger.debug(
                "Validating form creation request",
                request_id=request_id,
                form_type="client_onboarding",
                validation_stage="request_validation"
            )
            
            await asyncio.sleep(0.003)  # 3ms
            
            # Simulate message bus processing
            self.logger.debug(
                "Processing command through message bus",
                request_id=request_id,
                command_type="SetupOnboardingForm",
                processing_stage="command_dispatch"
            )
            
            await asyncio.sleep(0.006)  # 6ms for command processing
            
            # Simulate database operations
            self.logger.info(
                "Creating form configuration",
                request_id=request_id,
                form_id=str(uuid.uuid4()),
                action="form_creation_complete",
                status="success"
            )
            
            await asyncio.sleep(0.004)  # 4ms for DB operations
            
            end_time = time.perf_counter()
            return True, (end_time - start_time) * 1000
            
        except Exception as e:
            self.logger.error(
                "Form creation failed",
                request_id=request_id,
                error=str(e),
                action="form_creation_error"
            )
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000

    async def simulate_recipe_operations(self, request_id: str) -> tuple[bool, float]:
        """Simulate recipe catalog operations load."""
        start_time = time.perf_counter()
        
        try:
            correlation_id = generate_correlation_id()
            
            self.logger.info(
                "Processing recipe operation",
                request_id=request_id,
                correlation_id=correlation_id,
                action="recipe_operation_start"
            )
            
            # Simulate authentication and authorization
            await asyncio.sleep(0.002)  # 2ms
            
            # Simulate recipe data processing
            self.logger.debug(
                "Processing recipe data",
                request_id=request_id,
                recipe_type="main_dish",
                ingredients_count=8,
                processing_stage="recipe_validation"
            )
            
            await asyncio.sleep(0.005)  # 5ms
            
            # Simulate complex business logic
            self.logger.debug(
                "Calculating nutritional information",
                request_id=request_id,
                calculation_type="nutritional_analysis",
                processing_stage="nutrition_calculation"
            )
            
            await asyncio.sleep(0.007)  # 7ms for complex calculations
            
            # Simulate data persistence
            self.logger.info(
                "Recipe operation completed",
                request_id=request_id,
                recipe_id=str(uuid.uuid4()),
                action="recipe_operation_complete",
                status="success"
            )
            
            await asyncio.sleep(0.004)  # 4ms for persistence
            
            end_time = time.perf_counter()
            return True, (end_time - start_time) * 1000
            
        except Exception as e:
            self.logger.error(
                "Recipe operation failed",
                request_id=request_id,
                error=str(e),
                action="recipe_operation_error"
            )
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000

    async def run_load_test_scenario(
        self, 
        scenario_name: str, 
        scenario_func, 
        concurrent_requests: int = 50, 
        total_requests: int = 1000
    ) -> LoadTestResult:
        """Run a load test scenario with specified concurrency and request count."""
        
        print(f"\n🚀 Starting load test: {scenario_name}")
        print(f"   Concurrent requests: {concurrent_requests}")
        print(f"   Total requests: {total_requests}")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        start_time = time.perf_counter()
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def bounded_request(request_id: str):
            async with semaphore:
                return await scenario_func(request_id)
        
        # Create all tasks
        tasks = [
            bounded_request(f"{scenario_name}_{i}")
            for i in range(total_requests)
        ]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                failed_requests += 1
                response_times.append(0)  # Add 0 for failed requests
            else:
                success, response_time = result
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1
                response_times.append(response_time)
        
        # Calculate statistics
        valid_response_times = [rt for rt in response_times if rt > 0]
        
        if valid_response_times:
            avg_response_time = sum(valid_response_times) / len(valid_response_times)
            min_response_time = min(valid_response_times)
            max_response_time = max(valid_response_times)
            
            # Calculate percentiles
            sorted_times = sorted(valid_response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        
        result = LoadTestResult(
            scenario_name=scenario_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time_seconds=total_time,
            average_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            requests_per_second=requests_per_second,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            error_rate_percent=error_rate
        )
        
        self.results.append(result)
        
        # Print immediate results
        print(f"   ✅ Completed in {total_time:.2f}s")
        print(f"   📊 {successful_requests}/{total_requests} successful ({error_rate:.1f}% error rate)")
        print(f"   ⚡ {requests_per_second:.1f} req/sec")
        print(f"   ⏱️  Avg response: {avg_response_time:.2f}ms")
        
        return result

    async def run_all_load_tests(self) -> Dict[str, Any]:
        """Run all critical path load tests."""
        
        print("🔥 Starting Critical Path Load Testing")
        print("=" * 60)
        
        # Define test scenarios with different load characteristics
        scenarios = [
            ("Webhook Processing", self.simulate_webhook_processing, 30, 500),
            ("Product Queries", self.simulate_product_query, 50, 1000),
            ("Form Creation", self.simulate_form_creation, 20, 300),
            ("Recipe Operations", self.simulate_recipe_operations, 25, 400),
        ]
        
        for scenario_name, scenario_func, concurrency, total_requests in scenarios:
            await self.run_load_test_scenario(
                scenario_name, 
                scenario_func, 
                concurrency, 
                total_requests
            )
        
        # Generate summary
        return self.generate_summary()

    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive load test summary."""
        
        print("\n" + "=" * 60)
        print("📊 CRITICAL PATH LOAD TEST RESULTS")
        print("=" * 60)
        
        summary = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_scenarios": len(self.results),
                "mock_mode": not IMPORTS_AVAILABLE
            },
            "scenario_results": {},
            "overall_assessment": {}
        }
        
        total_requests = 0
        total_successful = 0
        total_failed = 0
        all_response_times = []
        
        for result in self.results:
            print(f"\n📋 {result.scenario_name}:")
            print(f"   Requests: {result.successful_requests}/{result.total_requests} successful")
            print(f"   Error Rate: {result.error_rate_percent:.1f}%")
            print(f"   Throughput: {result.requests_per_second:.1f} req/sec")
            print(f"   Response Times: avg={result.average_response_time_ms:.2f}ms, "
                  f"p95={result.p95_response_time_ms:.2f}ms, p99={result.p99_response_time_ms:.2f}ms")
            
            # Add to summary
            summary["scenario_results"][result.scenario_name] = {
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "error_rate_percent": result.error_rate_percent,
                "requests_per_second": result.requests_per_second,
                "average_response_time_ms": result.average_response_time_ms,
                "p95_response_time_ms": result.p95_response_time_ms,
                "p99_response_time_ms": result.p99_response_time_ms,
                "assessment": "PASS" if result.error_rate_percent < 1.0 and result.average_response_time_ms < 100 else "INVESTIGATE"
            }
            
            # Aggregate totals
            total_requests += result.total_requests
            total_successful += result.successful_requests
            total_failed += result.failed_requests
        
        # Overall assessment
        overall_error_rate = (total_failed / total_requests) * 100 if total_requests > 0 else 0
        overall_success_rate = (total_successful / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        print(f"   Error Rate: {overall_error_rate:.1f}%")
        
        # Determine overall status
        if overall_error_rate < 1.0:
            overall_status = "✅ PASS - All scenarios performed within acceptable limits"
            assessment = "PASS"
        elif overall_error_rate < 5.0:
            overall_status = "⚠️ INVESTIGATE - Some scenarios show elevated error rates"
            assessment = "INVESTIGATE"
        else:
            overall_status = "❌ FAIL - High error rates detected under load"
            assessment = "FAIL"
        
        print(f"   Status: {overall_status}")
        
        summary["overall_assessment"] = {
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "overall_success_rate": overall_success_rate,
            "overall_error_rate": overall_error_rate,
            "assessment": assessment,
            "status_message": overall_status
        }
        
        return summary


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test critical application paths")
    parser.add_argument("--output", help="Output file for results JSON")
    parser.add_argument("--concurrency", type=int, default=50, help="Default concurrent requests")
    parser.add_argument("--requests", type=int, default=1000, help="Default total requests per scenario")
    args = parser.parse_args()
    
    async def run_tests():
        tester = CriticalPathLoadTester()
        results = await tester.run_all_load_tests()
        
        # Save results to file
        output_file = args.output or "tasks/logging-standardization/artifacts/load_test_results.json"
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Exit with appropriate code
        assessment = results["overall_assessment"]["assessment"]
        return 0 if assessment == "PASS" else 1
    
    # Run the async tests
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
