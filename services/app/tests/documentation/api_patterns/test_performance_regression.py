"""
Performance Regression Tests for TypeAdapter Patterns

This module contains automated tests that fail if TypeAdapter performance degrades
beyond acceptable thresholds. Since no CI/CD pipeline exists, these tests should be
run manually before major releases or when modifying TypeAdapter patterns.

Usage:
    # Run all performance regression tests
    poetry run python pytest tests/documentation/api_patterns/test_performance_regression.py -v
    
    # Run with benchmark output
    poetry run python pytest tests/documentation/api_patterns/test_performance_regression.py --benchmark-only
    
    # Run specific regression test
    poetry run python pytest tests/documentation/api_patterns/test_performance_regression.py::TestTypeAdapterPerformanceRegression::test_recipe_list_adapter_regression -v

Test Philosophy:
- Tests fail if performance degrades beyond baseline metrics
- Memory usage monitoring prevents memory leaks
- Thread safety validation prevents concurrency issues
- Tests use realistic data scenarios matching production usage
"""

import json
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List
import warnings

# TypeAdapter imports
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import TagFrozensetAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import RecipeListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import IngredientListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import RatingListAdapter
from src.contexts.seedwork.shared.adapters.api_schemas.type_adapters import (
    JsonSafeListAdapter,
    RoleSetAdapter,
    UniqueCollectionAdapter
)

# Schema imports for test data
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.api_seed_role import ApiSeedRole

# Data factory imports for realistic test data
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.meal_benchmark_data_factories import (
    create_api_recipe,
    reset_counters
)


class TestTypeAdapterPerformanceRegression:
    """Performance regression tests that fail if TypeAdapter performance degrades."""
    
    # Baseline performance thresholds (based on Phase 1.3.1 results)
    # These should be updated if baseline performance legitimately improves
    RECIPE_LIST_10_ITEMS_MAX_MS = 3.0      # PRD requirement: < 3ms for 10 recipes
    RECIPE_LIST_100_ITEMS_MAX_MS = 30.0    # Scaling: 10x data allows 10x time
    TAG_FROZENSET_10_ITEMS_MAX_MS = 3.0    # Same as recipe requirement
    INGREDIENT_LIST_10_ITEMS_MAX_MS = 3.0  # Same performance expectation
    RATING_LIST_10_ITEMS_MAX_MS = 3.0      # Same performance expectation
    
    # Memory thresholds
    MAX_MEMORY_GROWTH_MB = 5.0             # Maximum acceptable memory growth
    MAX_MEMORY_LEAK_MB = 1.0               # Memory that doesn't get garbage collected
    
    # Thread safety thresholds
    MAX_CONCURRENT_VALIDATION_MS = 10.0    # Maximum time for concurrent validation
    
    def setup_method(self):
        """Set up test data for regression testing."""
        # Reset counters for deterministic data
        reset_counters()
        
        # 10-item test data (PRD target size)
        self.tag_data_10 = [
            {"key": f"tag{i}", "value": f"value{i}", "author_id": f"user{i}", "type": "category"}
            for i in range(10)
        ]
        
        self.ingredient_data_10 = [
            {
                "name": f"Ingredient {i}",
                "quantity": 100.0,
                "unit": "g",
                "position": i + 1,
                "full_text": f"100g of Ingredient {i}",
                "product_id": "550e8400-e29b-41d4-a716-446655440000"
            }
            for i in range(10)
        ]
        
        self.rating_data_10 = [
            {
                "user_id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                "recipe_id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                "taste": 4,
                "convenience": 3,
                "comment": f"Great recipe {i}!"
            }
            for i in range(10)
        ]
        
        self.role_data_10 = [
            {"name": f"role_{i}", "permissions": ["read", "write"]}
            for i in range(10)
        ]
        
        # Recipe test data - varying sizes
        self.recipe_data_10 = [create_api_recipe() for _ in range(10)]
        self.recipe_data_100 = [create_api_recipe() for _ in range(100)]
    
    def _serialize_recipes_to_json(self, recipes: List[ApiRecipe]) -> str:
        """Helper to serialize recipes to JSON."""
        from pydantic import TypeAdapter
        list_adapter = TypeAdapter(List[ApiRecipe])
        return list_adapter.dump_json(recipes).decode()
    
    def _measure_operation_time(self, operation_func, iterations: int = 10) -> float:
        """Measure average operation time in milliseconds."""
        start_time = time.perf_counter()
        for _ in range(iterations):
            operation_func()
        end_time = time.perf_counter()
        return ((end_time - start_time) / iterations) * 1000  # Convert to ms

    def test_recipe_list_adapter_regression(self):
        """REGRESSION: RecipeListAdapter performance must not degrade below baseline."""
        json_data_10 = self._serialize_recipes_to_json(self.recipe_data_10)
        json_data_100 = self._serialize_recipes_to_json(self.recipe_data_100)
        
        # Test 10 items (PRD requirement)
        def validate_10_recipes():
            return RecipeListAdapter.validate_json(json_data_10)
        
        time_10_items = self._measure_operation_time(validate_10_recipes, iterations=20)
        
        # Test 100 items (scaling test)
        def validate_100_recipes():
            return RecipeListAdapter.validate_json(json_data_100)
        
        time_100_items = self._measure_operation_time(validate_100_recipes, iterations=5)
        
        # Regression assertions - these will FAIL if performance degrades
        assert time_10_items < self.RECIPE_LIST_10_ITEMS_MAX_MS, \
            f"REGRESSION: RecipeListAdapter (10 items) took {time_10_items:.2f}ms, exceeds baseline of {self.RECIPE_LIST_10_ITEMS_MAX_MS}ms"
        
        assert time_100_items < self.RECIPE_LIST_100_ITEMS_MAX_MS, \
            f"REGRESSION: RecipeListAdapter (100 items) took {time_100_items:.2f}ms, exceeds baseline of {self.RECIPE_LIST_100_ITEMS_MAX_MS}ms"
        
        # Log current performance
        print(f"\n✓ RecipeListAdapter Performance Regression Check:")
        print(f"  10 items: {time_10_items:.2f}ms (limit: {self.RECIPE_LIST_10_ITEMS_MAX_MS}ms)")
        print(f"  100 items: {time_100_items:.2f}ms (limit: {self.RECIPE_LIST_100_ITEMS_MAX_MS}ms)")

    def test_tag_frozenset_adapter_regression(self):
        """REGRESSION: TagFrozensetAdapter performance must not degrade below baseline."""
        json_data = json.dumps(self.tag_data_10)
        
        def validate_tags():
            return TagFrozensetAdapter.validate_json(json_data)
        
        avg_time = self._measure_operation_time(validate_tags, iterations=50)
        
        # Regression assertion
        assert avg_time < self.TAG_FROZENSET_10_ITEMS_MAX_MS, \
            f"REGRESSION: TagFrozensetAdapter took {avg_time:.2f}ms, exceeds baseline of {self.TAG_FROZENSET_10_ITEMS_MAX_MS}ms"
        
        print(f"\n✓ TagFrozensetAdapter Performance Regression Check:")
        print(f"  10 items: {avg_time:.2f}ms (limit: {self.TAG_FROZENSET_10_ITEMS_MAX_MS}ms)")

    def test_ingredient_list_adapter_regression(self):
        """REGRESSION: IngredientListAdapter performance must not degrade below baseline."""
        json_data = json.dumps(self.ingredient_data_10)
        
        def validate_ingredients():
            return IngredientListAdapter.validate_json(json_data)
        
        avg_time = self._measure_operation_time(validate_ingredients, iterations=50)
        
        # Regression assertion
        assert avg_time < self.INGREDIENT_LIST_10_ITEMS_MAX_MS, \
            f"REGRESSION: IngredientListAdapter took {avg_time:.2f}ms, exceeds baseline of {self.INGREDIENT_LIST_10_ITEMS_MAX_MS}ms"
        
        print(f"\n✓ IngredientListAdapter Performance Regression Check:")
        print(f"  10 items: {avg_time:.2f}ms (limit: {self.INGREDIENT_LIST_10_ITEMS_MAX_MS}ms)")

    def test_rating_list_adapter_regression(self):
        """REGRESSION: RatingListAdapter performance must not degrade below baseline."""
        json_data = json.dumps(self.rating_data_10)
        
        def validate_ratings():
            return RatingListAdapter.validate_json(json_data)
        
        avg_time = self._measure_operation_time(validate_ratings, iterations=50)
        
        # Regression assertion
        assert avg_time < self.RATING_LIST_10_ITEMS_MAX_MS, \
            f"REGRESSION: RatingListAdapter took {avg_time:.2f}ms, exceeds baseline of {self.RATING_LIST_10_ITEMS_MAX_MS}ms"
        
        print(f"\n✓ RatingListAdapter Performance Regression Check:")
        print(f"  10 items: {avg_time:.2f}ms (limit: {self.RATING_LIST_10_ITEMS_MAX_MS}ms)")

    def test_memory_usage_regression(self):
        """REGRESSION: TypeAdapter memory usage must not exceed acceptable growth."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory profiling")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform intensive validation operations
        json_data = self._serialize_recipes_to_json(self.recipe_data_10)
        
        for _ in range(1000):  # 1000 iterations to detect memory leaks
            RecipeListAdapter.validate_json(json_data)
            TagFrozensetAdapter.validate_json(json.dumps(self.tag_data_10))
            IngredientListAdapter.validate_json(json.dumps(self.ingredient_data_10))
        
        # Measure memory after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Regression assertion
        assert memory_growth < self.MAX_MEMORY_GROWTH_MB, \
            f"REGRESSION: Memory grew by {memory_growth:.2f}MB, exceeds limit of {self.MAX_MEMORY_GROWTH_MB}MB"
        
        # Force garbage collection and check for memory leaks
        import gc
        gc.collect()
        
        gc_memory = process.memory_info().rss / 1024 / 1024  # MB
        potential_leak = gc_memory - initial_memory
        
        if potential_leak > self.MAX_MEMORY_LEAK_MB:
            warnings.warn(
                f"Potential memory leak detected: {potential_leak:.2f}MB not freed after garbage collection",
                UserWarning
            )
        
        print(f"\n✓ Memory Usage Regression Check:")
        print(f"  Memory growth: {memory_growth:.2f}MB (limit: {self.MAX_MEMORY_GROWTH_MB}MB)")
        print(f"  After GC: {potential_leak:.2f}MB (leak threshold: {self.MAX_MEMORY_LEAK_MB}MB)")

    def test_thread_safety_regression(self):
        """REGRESSION: TypeAdapter thread safety must not degrade."""
        json_data = self._serialize_recipes_to_json(self.recipe_data_10)
        
        def concurrent_validation():
            """Perform validation in a thread."""
            results = []
            for _ in range(10):
                result = RecipeListAdapter.validate_json(json_data)
                results.append(len(result))
            return results
        
        # Measure concurrent validation time
        start_time = time.perf_counter()
        
        # Test with 20 threads performing 10 validations each = 200 total operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(concurrent_validation) for _ in range(20)]
            thread_results = [future.result() for future in futures]
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # ms
        
        # Verify all operations completed successfully
        total_operations = sum(len(result) for result in thread_results)
        assert total_operations == 200, f"Expected 200 operations, got {total_operations}"
        
        # Verify all results are correct
        for thread_result in thread_results:
            assert len(thread_result) == 10  # 10 validations per thread
            assert all(count == 10 for count in thread_result)  # Each validation returns 10 recipes
        
        # Regression assertion for concurrent performance
        assert total_time < self.MAX_CONCURRENT_VALIDATION_MS * 1000, \
            f"REGRESSION: Concurrent validation took {total_time:.2f}ms, exceeds limit of {self.MAX_CONCURRENT_VALIDATION_MS * 1000}ms"
        
        print(f"\n✓ Thread Safety Regression Check:")
        print(f"  20 threads × 10 validations = 200 operations: {total_time:.2f}ms")
        print(f"  Average per operation: {total_time / 200:.2f}ms")
        print(f"  Limit: {self.MAX_CONCURRENT_VALIDATION_MS * 1000}ms total")

    def test_singleton_pattern_stability_regression(self):
        """REGRESSION: Singleton pattern performance benefits must be maintained."""
        from pydantic import TypeAdapter
        
        json_data = json.dumps(self.tag_data_10)
        iterations = 100
        
        # Test recreation pattern (anti-pattern)
        start_time = time.perf_counter()
        for _ in range(iterations):
            adapter = TypeAdapter(list[dict])  # Recreate each time
            adapter.validate_json(json_data)
        recreation_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Test singleton pattern
        start_time = time.perf_counter()
        for _ in range(iterations):
            JsonSafeListAdapter.validate_json(json_data)  # Use singleton
        singleton_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Calculate performance benefit
        improvement_factor = recreation_time / singleton_time
        
        # Regression assertion - singleton must be significantly faster
        assert improvement_factor > 2.0, \
            f"REGRESSION: Singleton pattern only {improvement_factor:.2f}x faster than recreation, should be >2x"
        
        # Additional check - singleton should be absolutely fast
        avg_singleton_time = singleton_time / iterations
        assert avg_singleton_time < 0.5, \
            f"REGRESSION: Singleton validation took {avg_singleton_time:.2f}ms per operation, too slow"
        
        print(f"\n✓ Singleton Pattern Regression Check:")
        print(f"  Recreation pattern: {recreation_time:.2f}ms total")
        print(f"  Singleton pattern: {singleton_time:.2f}ms total")
        print(f"  Improvement factor: {improvement_factor:.2f}x (required: >2.0x)")
        print(f"  Singleton per operation: {avg_singleton_time:.2f}ms (limit: <0.5ms)")

    def test_unique_collection_adapter_caching_regression(self):
        """REGRESSION: UniqueCollectionAdapter caching performance must be maintained."""
        adapter = UniqueCollectionAdapter(
            item_type=str,
            key_func=lambda x: x,
            collection_name="regression_test"
        )
        
        test_data = ["item1", "item2", "item3"]
        
        # First validation (cache miss)
        start_time = time.perf_counter()
        adapter.validate_python(test_data)
        first_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Subsequent validations (cache hit)
        start_time = time.perf_counter()
        for _ in range(1000):
            adapter.validate_python(test_data)
        cached_time = (time.perf_counter() - start_time) * 1000  # ms
        avg_cached_time = cached_time / 1000
        
        # Regression assertions
        assert avg_cached_time < 0.01, \
            f"REGRESSION: Cached validation took {avg_cached_time:.3f}ms, should be <0.01ms"
        
        # Caching should provide significant speedup
        speedup_factor = first_time / avg_cached_time
        assert speedup_factor > 10.0, \
            f"REGRESSION: Caching only provides {speedup_factor:.1f}x speedup, should be >10x"
        
        print(f"\n✓ UniqueCollectionAdapter Caching Regression Check:")
        print(f"  First validation: {first_time:.3f}ms")
        print(f"  Cached validation: {avg_cached_time:.3f}ms average")
        print(f"  Speedup factor: {speedup_factor:.1f}x (required: >10x)")


class TestTypeAdapterRegressionReporting:
    """Tests that generate regression reports for manual analysis."""
    
    def test_generate_performance_regression_report(self):
        """Generate a comprehensive performance report for manual review."""
        print("\n" + "="*80)
        print("TYPEADAPTER PERFORMANCE REGRESSION REPORT")
        print("="*80)
        print("Generated for manual review - run this test periodically")
        print("All tests above should PASS if no performance regressions exist")
        print("")
        
        # Instructions for manual use
        print("USAGE INSTRUCTIONS:")
        print("1. Run this file before major releases:")
        print("   poetry run python pytest tests/documentation/api_patterns/test_performance_regression.py -v")
        print("")
        print("2. Run with benchmark details:")
        print("   poetry run python pytest tests/documentation/api_patterns/test_performance_regression.py --benchmark-only")
        print("")
        print("3. If any test FAILS:")
        print("   - Investigate what changed since last successful run")
        print("   - Determine if performance degradation is acceptable")
        print("   - Update baseline thresholds if improved performance is verified")
        print("   - Never lower thresholds without understanding root cause")
        print("")
        
        # Current baseline summary
        test_instance = TestTypeAdapterPerformanceRegression()
        print("CURRENT BASELINE THRESHOLDS:")
        print(f"  RecipeListAdapter (10 items): < {test_instance.RECIPE_LIST_10_ITEMS_MAX_MS}ms")
        print(f"  RecipeListAdapter (100 items): < {test_instance.RECIPE_LIST_100_ITEMS_MAX_MS}ms")
        print(f"  TagFrozensetAdapter (10 items): < {test_instance.TAG_FROZENSET_10_ITEMS_MAX_MS}ms")
        print(f"  IngredientListAdapter (10 items): < {test_instance.INGREDIENT_LIST_10_ITEMS_MAX_MS}ms")
        print(f"  RatingListAdapter (10 items): < {test_instance.RATING_LIST_10_ITEMS_MAX_MS}ms")
        print(f"  Memory growth limit: < {test_instance.MAX_MEMORY_GROWTH_MB}MB")
        print(f"  Memory leak threshold: < {test_instance.MAX_MEMORY_LEAK_MB}MB")
        print(f"  Concurrent validation: < {test_instance.MAX_CONCURRENT_VALIDATION_MS}s")
        print("")
        
        print("INTEGRATION WITH DOCUMENTATION PROJECT:")
        print("- These tests validate that documented TypeAdapter patterns maintain performance")
        print("- Before documenting new patterns, ensure they pass these regression tests")
        print("- Phase 2+ documentation must reference these performance guarantees")
        print("="*80)
        
        # This test always passes - it's just for reporting
        assert True, "Performance regression report generated successfully" 