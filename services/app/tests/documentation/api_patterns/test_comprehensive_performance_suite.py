"""
Comprehensive Performance Test Suite for API Schema Pattern Documentation

This module implements comprehensive performance testing for all documented patterns:
1. TypeAdapter performance regression testing
2. Memory usage pattern validation  
3. Stress testing for large data scenarios
4. Performance benchmarking for all conversion patterns
5. Concurrent access performance validation

Tests validate that all documented patterns meet performance requirements.
Target: All patterns must meet or exceed baseline performance metrics.
"""

import pytest
import time
import gc
import threading
import psutil
import os
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all schema classes and TypeAdapters for performance testing
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag, TagFrozensetAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient, IngredientListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating, RatingListAdapter
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole
from src.contexts.seedwork.shared.adapters.api_schemas.type_adapters import RoleSetAdapter


@dataclass
class PerformanceResult:
    """Results from performance testing."""
    test_name: str
    operation_type: str
    avg_time_ms: float
    max_time_ms: float
    min_time_ms: float
    memory_usage_mb: float
    iterations: int
    passed: bool
    failure_reason: Optional[str] = None


@dataclass
class StressTestResult:
    """Results from stress testing with large datasets."""
    test_name: str
    dataset_size: int
    total_time_ms: float
    throughput_ops_per_sec: float
    memory_peak_mb: float
    passed: bool
    failure_reason: Optional[str] = None


class ComprehensivePerformanceSuite:
    """Comprehensive performance testing suite for API schema patterns."""
    
    def __init__(self):
        """Initialize performance suite with baseline metrics."""
        self.baseline_metrics = {
            "single_validation_ms": 3.0,  # From PRD requirement
            "bulk_validation_per_item_ms": 0.5,  # For large collections
            "memory_growth_limit_mb": 10.0,  # Memory growth limit
            "concurrent_degradation_limit": 2.0,  # Max 2x slower with concurrency
            "stress_test_throughput_min": 100.0  # Minimum ops/sec for stress tests
        }
        
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def measure_operation_performance(
        self,
        operation_func,
        iterations: int = 100,
        warmup_iterations: int = 10
    ) -> PerformanceResult:
        """Measure performance of an operation with statistics."""
        operation_name = getattr(operation_func, '__name__', 'unknown_operation')
        
        # Warmup
        for _ in range(warmup_iterations):
            try:
                operation_func()
            except Exception:
                pass
        
        # Measure memory before
        gc.collect()
        memory_before = self.get_memory_usage_mb()
        
        # Measure execution times
        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                operation_func()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to ms
            except Exception as e:
                return PerformanceResult(
                    test_name=operation_name,
                    operation_type="operation",
                    avg_time_ms=0.0,
                    max_time_ms=0.0,
                    min_time_ms=0.0,
                    memory_usage_mb=0.0,
                    iterations=0,
                    passed=False,
                    failure_reason=f"Operation failed: {str(e)}"
                )
        
        # Measure memory after
        gc.collect()
        memory_after = self.get_memory_usage_mb()
        memory_growth = memory_after - memory_before
        
        # Calculate statistics
        avg_time_ms = sum(times) / len(times)
        max_time_ms = max(times)
        min_time_ms = min(times)
        
        # Determine if test passed
        passed = (
            avg_time_ms <= self.baseline_metrics["single_validation_ms"] and
            memory_growth <= self.baseline_metrics["memory_growth_limit_mb"]
        )
        
        return PerformanceResult(
            test_name=operation_name,
            operation_type="operation",
            avg_time_ms=avg_time_ms,
            max_time_ms=max_time_ms,
            min_time_ms=min_time_ms,
            memory_usage_mb=memory_growth,
            iterations=iterations,
            passed=passed,
            failure_reason=None if passed else f"Avg time {avg_time_ms:.2f}ms > {self.baseline_metrics['single_validation_ms']}ms or memory growth {memory_growth:.2f}MB > {self.baseline_metrics['memory_growth_limit_mb']}MB"
        )


class TestComprehensivePerformanceSuite:
    """Test suite for comprehensive performance validation."""
    
    @pytest.fixture(autouse=True)
    def setup_performance_suite(self):
        """Setup performance suite for each test."""
        self.suite = ComprehensivePerformanceSuite()
        
    def test_single_schema_validation_performance(self, sample_tag_domain):
        """Test single schema validation performance against baseline."""
        test_data = {
            "key": sample_tag_domain.key,
            "value": sample_tag_domain.value,
            "author_id": sample_tag_domain.author_id,
            "type": sample_tag_domain.type
        }
        
        def validate_operation():
            return ApiTag.model_validate(test_data)
        
        result = self.suite.measure_operation_performance(validate_operation, iterations=1000)
        
        assert result.passed, f"Single validation performance failed: {result.failure_reason}"
        assert result.avg_time_ms < 3.0, f"Average validation time {result.avg_time_ms:.2f}ms exceeds 3ms requirement"
        
        print(f"\n=== Single Schema Validation Performance ===")
        print(f"Average time: {result.avg_time_ms:.2f}ms")
        print(f"Memory growth: {result.memory_usage_mb:.2f}MB")
        print(f"Iterations: {result.iterations}")

    def test_typeadapter_singleton_performance(self, sample_api_tags_collection):
        """Test TypeAdapter singleton pattern performance."""
        tag_data = [
            {"key": tag.key, "value": tag.value, "author_id": tag.author_id, "type": tag.type}
            for tag in sample_api_tags_collection
        ]
        
        def singleton_operation():
            return TagFrozensetAdapter.validate_python(tag_data)
        
        result = self.suite.measure_operation_performance(singleton_operation, iterations=1000)
        
        assert result.passed, f"TypeAdapter singleton performance failed: {result.failure_reason}"
        
        print(f"\n=== TypeAdapter Singleton Performance ===")
        print(f"Average time: {result.avg_time_ms:.2f}ms")
        print(f"Memory growth: {result.memory_usage_mb:.2f}MB")

    def test_bulk_validation_performance(self, large_collection_data):
        """Test bulk validation performance with large datasets."""
        ingredient_data = large_collection_data["ingredients"][:10]  # Test with 10 items
        
        def bulk_validation():
            return IngredientListAdapter.validate_python(ingredient_data)
        
        result = self.suite.measure_operation_performance(bulk_validation, iterations=100)
        
        # For bulk operations, allow more time per item
        max_time_per_item = len(ingredient_data) * self.suite.baseline_metrics["bulk_validation_per_item_ms"]
        
        assert result.avg_time_ms <= max_time_per_item, f"Bulk validation {result.avg_time_ms:.2f}ms exceeds {max_time_per_item}ms limit"
        
        print(f"\n=== Bulk Validation Performance ({len(ingredient_data)} items) ===")
        print(f"Average time: {result.avg_time_ms:.2f}ms")
        print(f"Time per item: {result.avg_time_ms / len(ingredient_data):.2f}ms")
        print(f"Memory growth: {result.memory_usage_mb:.2f}MB")

    def test_four_layer_conversion_performance(self, sample_tag_domain):
        """Test complete four-layer conversion cycle performance."""
        def conversion_cycle():
            # Domain → API
            api_obj = ApiTag.from_domain(sample_tag_domain)
            
            # API → ORM kwargs
            orm_kwargs = api_obj.to_orm_kwargs()
            
            # Simulate ORM → API (mock ORM object)
            from unittest.mock import Mock
            mock_orm = Mock()
            for key, value in orm_kwargs.items():
                setattr(mock_orm, key, value)
            
            # ORM → API
            reconstructed_api = ApiTag.from_orm_model(mock_orm)
            
            # API → Domain
            return reconstructed_api.to_domain()
        
        result = self.suite.measure_operation_performance(conversion_cycle, iterations=500)
        
        # Allow more time for complete conversion cycle
        max_conversion_time = 10.0  # 10ms for complete cycle
        assert result.avg_time_ms <= max_conversion_time, f"Conversion cycle {result.avg_time_ms:.2f}ms exceeds {max_conversion_time}ms limit"
        
        print(f"\n=== Four-Layer Conversion Performance ===")
        print(f"Average time: {result.avg_time_ms:.2f}ms")
        print(f"Memory growth: {result.memory_usage_mb:.2f}MB")

    def test_concurrent_access_performance(self, sample_ingredient_data):
        """Test TypeAdapter performance under concurrent access."""
        num_threads = 10
        operations_per_thread = 50
        
        def concurrent_validation():
            return ApiIngredient.model_validate(sample_ingredient_data)
        
        # Measure single-threaded baseline
        baseline_result = self.suite.measure_operation_performance(
            concurrent_validation, iterations=num_threads * operations_per_thread
        )
        
        # Measure concurrent performance
        start_time = time.perf_counter()
        memory_before = self.suite.get_memory_usage_mb()
        
        def thread_worker():
            times = []
            for _ in range(operations_per_thread):
                op_start = time.perf_counter()
                concurrent_validation()
                op_end = time.perf_counter()
                times.append((op_end - op_start) * 1000)
            return times
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(thread_worker) for _ in range(num_threads)]
            all_times = []
            for future in as_completed(futures):
                all_times.extend(future.result())
        
        end_time = time.perf_counter()
        memory_after = self.suite.get_memory_usage_mb()
        
        concurrent_avg_time = sum(all_times) / len(all_times)
        concurrent_memory_growth = memory_after - memory_before
        
        # Concurrent performance shouldn't degrade more than 2x
        degradation_factor = concurrent_avg_time / baseline_result.avg_time_ms
        
        assert degradation_factor <= self.suite.baseline_metrics["concurrent_degradation_limit"], \
            f"Concurrent degradation {degradation_factor:.1f}x exceeds {self.suite.baseline_metrics['concurrent_degradation_limit']}x limit"
        
        print(f"\n=== Concurrent Access Performance ===")
        print(f"Baseline avg: {baseline_result.avg_time_ms:.2f}ms")
        print(f"Concurrent avg: {concurrent_avg_time:.2f}ms")
        print(f"Degradation factor: {degradation_factor:.1f}x")
        print(f"Memory growth: {concurrent_memory_growth:.2f}MB")

    def test_stress_test_large_collections(self, large_collection_data):
        """Stress test with large collections to validate scalability."""
        def run_stress_test(dataset_name: str, data: List[Dict], adapter, max_size: int = 100):
            """Run stress test for a specific dataset and adapter."""
            memory_before = self.suite.get_memory_usage_mb()
            start_time = time.perf_counter()
            
            try:
                # Test with increasing sizes
                for size in [10, 25, 50, max_size]:
                    subset = data[:size]
                    result = adapter.validate_python(subset)
                    assert len(result) == size, f"Expected {size} items, got {len(result)}"
                
                end_time = time.perf_counter()
                memory_after = self.suite.get_memory_usage_mb()
                
                total_time_ms = (end_time - start_time) * 1000
                throughput = (max_size * 4) / (total_time_ms / 1000)  # 4 iterations total
                memory_peak = memory_after - memory_before
                
                passed = throughput >= self.suite.baseline_metrics["stress_test_throughput_min"]
                
                return StressTestResult(
                    test_name=dataset_name,
                    dataset_size=max_size,
                    total_time_ms=total_time_ms,
                    throughput_ops_per_sec=throughput,
                    memory_peak_mb=memory_peak,
                    passed=passed,
                    failure_reason=None if passed else f"Throughput {throughput:.1f} ops/sec < {self.suite.baseline_metrics['stress_test_throughput_min']} ops/sec"
                )
                
            except Exception as e:
                return StressTestResult(
                    test_name=dataset_name,
                    dataset_size=max_size,
                    total_time_ms=0.0,
                    throughput_ops_per_sec=0.0,
                    memory_peak_mb=0.0,
                    passed=False,
                    failure_reason=f"Stress test failed: {str(e)}"
                )
        
        # Run stress tests for each collection type
        stress_results = []
        
        # Test ingredient collections
        ingredient_result = run_stress_test(
            "ingredients", 
            large_collection_data["ingredients"], 
            IngredientListAdapter,
            max_size=50  # Reduce size for performance
        )
        stress_results.append(ingredient_result)
        
        # Test tag collections
        tag_result = run_stress_test(
            "tags",
            large_collection_data["tags"],
            TagFrozensetAdapter,
            max_size=50
        )
        stress_results.append(tag_result)
        
        # Validate all stress tests passed
        failed_tests = [result for result in stress_results if not result.passed]
        assert len(failed_tests) == 0, f"Stress tests failed: {[test.failure_reason for test in failed_tests]}"
        
        print(f"\n=== Stress Test Results ===")
        for result in stress_results:
            print(f"{result.test_name}: {result.throughput_ops_per_sec:.1f} ops/sec, {result.memory_peak_mb:.2f}MB peak")

    def test_memory_usage_patterns(self, large_collection_data):
        """Test memory usage patterns for potential memory leaks."""
        iterations = 20
        memory_samples = []
        
        ingredient_data = large_collection_data["ingredients"][:10]
        
        for i in range(iterations):
            # Perform operations
            result = IngredientListAdapter.validate_python(ingredient_data)
            
            # Sample memory every few iterations
            if i % 5 == 0:
                gc.collect()  # Force garbage collection
                memory_mb = self.suite.get_memory_usage_mb()
                memory_samples.append(memory_mb)
        
        # Check for memory growth trend
        if len(memory_samples) >= 3:
            initial_memory = memory_samples[0]
            final_memory = memory_samples[-1]
            memory_growth = final_memory - initial_memory
            
            # Allow some memory growth but flag significant increases
            max_allowed_growth = 20.0  # 20MB
            assert memory_growth <= max_allowed_growth, \
                f"Memory growth {memory_growth:.2f}MB exceeds {max_allowed_growth}MB limit. Possible memory leak."
        
        print(f"\n=== Memory Usage Pattern ===")
        print(f"Memory samples: {[f'{mem:.1f}MB' for mem in memory_samples]}")
        if len(memory_samples) >= 2:
            print(f"Memory growth: {memory_samples[-1] - memory_samples[0]:.1f}MB")

    @pytest.mark.integration
    def test_comprehensive_performance_report(self, large_collection_data, sample_tag_domain, sample_ingredient_data):
        """Generate comprehensive performance report for all patterns."""
        print(f"\n{'='*60}")
        print("COMPREHENSIVE PERFORMANCE REPORT")
        print(f"{'='*60}")
        
        # Run all performance tests and collect results
        all_results = []
        
        # Single validation test
        tag_data = {
            "key": sample_tag_domain.key,
            "value": sample_tag_domain.value,
            "author_id": sample_tag_domain.author_id,
            "type": sample_tag_domain.type
        }
        
        def tag_validation():
            return ApiTag.model_validate(tag_data)
        
        tag_result = self.suite.measure_operation_performance(tag_validation, iterations=1000)
        all_results.append(("Single Tag Validation", tag_result))
        
        # Ingredient validation test
        def ingredient_validation():
            return ApiIngredient.model_validate(sample_ingredient_data)
        
        ingredient_result = self.suite.measure_operation_performance(ingredient_validation, iterations=1000)
        all_results.append(("Single Ingredient Validation", ingredient_result))
        
        # TypeAdapter tests
        ingredient_bulk_data = large_collection_data["ingredients"][:5]
        
        def bulk_ingredient_validation():
            return IngredientListAdapter.validate_python(ingredient_bulk_data)
        
        bulk_result = self.suite.measure_operation_performance(bulk_ingredient_validation, iterations=500)
        all_results.append(("Bulk Ingredient Validation (5 items)", bulk_result))
        
        # Report results
        print(f"\nPerformance Test Results:")
        print(f"{'Test Name':<40} {'Avg Time':<12} {'Status':<8} {'Memory':<10}")
        print(f"{'-'*70}")
        
        passed_tests = 0
        total_tests = 0
        
        for test_name, result in all_results:
            status = "PASS" if result.passed else "FAIL"
            if result.passed:
                passed_tests += 1
            total_tests += 1
            
            print(f"{test_name:<40} {result.avg_time_ms:<11.2f}ms {status:<8} {result.memory_usage_mb:<9.1f}MB")
        
        print(f"{'-'*70}")
        print(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        # Performance baselines summary
        print(f"\nPerformance Baselines:")
        print(f"  Single validation: < {self.suite.baseline_metrics['single_validation_ms']}ms")
        print(f"  Memory growth: < {self.suite.baseline_metrics['memory_growth_limit_mb']}MB")
        print(f"  Bulk validation: < {self.suite.baseline_metrics['bulk_validation_per_item_ms']}ms per item")
        
        # Assert overall performance compliance
        performance_compliance = passed_tests / total_tests
        assert performance_compliance >= 0.8, f"Performance compliance {performance_compliance:.1%} below 80% threshold" 