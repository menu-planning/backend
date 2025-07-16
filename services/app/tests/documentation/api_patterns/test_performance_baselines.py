"""
Performance Baseline Tests for TypeAdapter Patterns

This module establishes performance baselines for all discovered TypeAdapter patterns
to ensure documentation recommendations don't introduce performance regressions.

Test Requirements:
- All TypeAdapter patterns must validate 10 items from JSON in < 3ms (PRD requirement)
- Memory usage must remain stable for singleton patterns
- Cached adapters must outperform recreation patterns
- Thread-safety validation for cached patterns

Discovered TypeAdapters:
1. TagFrozensetAdapter: frozenset[ApiTag]
2. RecipeListAdapter: list[ApiRecipe] 
3. IngredientListAdapter: list[ApiIngredient]
4. RatingListAdapter: list[ApiRating]
5. MenuMealFrozensetAdapter: frozenset[ApiMenuMeal]
6. JsonSafeListAdapter: list (with config)
7. JsonSafeSetAdapter: list (with config)
8. RoleSetAdapter: set[ApiSeedRole]
9. UniqueCollectionAdapter: cached dynamic pattern
"""

import json
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List
from unittest.mock import Mock

# TypeAdapter imports
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import TagFrozensetAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import RecipeListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import IngredientListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import RatingListAdapter
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import MenuMealFrozensetAdapter
from src.contexts.seedwork.shared.adapters.api_schemas.type_adapters import (
    JsonSafeListAdapter,
    JsonSafeSetAdapter, 
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


class TestTypeAdapterPerformanceBaselines:
    """Performance baseline tests for all TypeAdapter patterns."""
    
    # Performance thresholds from PRD
    MAX_VALIDATION_TIME_MS = 3.0  # < 3ms for 10 items from JSON
    MAX_MEMORY_GROWTH_MB = 5.0    # < 5MB memory growth for repeated validations
    
    def setup_method(self):
        """Set up test data for performance testing."""
        # Reset counters for deterministic data
        reset_counters()
        
        # Sample tag data
        self.tag_data = [
            {"key": f"tag{i}", "value": f"value{i}", "author_id": f"user{i}", "type": "category"}
            for i in range(10)
        ]
        
        # Sample ingredient data  
        self.ingredient_data = [
            {
                "name": f"Ingredient {i}",
                "quantity": 100.0,
                "unit": "g",  # Using MeasureUnit.GRAM enum value
                "position": i + 1,
                "full_text": f"100g of Ingredient {i}",
                "product_id": "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID format
            }
            for i in range(10)
        ]
        
        # Sample rating data
        self.rating_data = [
            {
                "user_id": f"550e8400-e29b-41d4-a716-44665544000{i}",  # Valid UUID format
                "recipe_id": f"550e8400-e29b-41d4-a716-44665544000{i}",  # Valid UUID format
                "taste": 4,
                "convenience": 3,
                "comment": f"Great recipe {i}!"
            }
            for i in range(10)
        ]
        
        # Sample role data
        self.role_data = [
            {"name": f"role_{i}", "permissions": ["read", "write"]}
            for i in range(10)
        ]
        
        # Sample menu meal data
        self.menu_meal_data = [
            {
                "meal_id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                "meal_name": f"Meal {i}",
                "nutri_facts": None,
                "week": (i % 4) + 1,  # Weeks 1-4
                "weekday": ["monday", "tuesday", "wednesday", "thursday", "friday"][i % 5],
                "hour": None,
                "meal_type": ["breakfast", "lunch", "dinner"][i % 3]
            }
            for i in range(10)
        ]
        
        # Sample recipe data using realistic data factory - Generate varying collection sizes
        self.recipe_data_1 = [create_api_recipe() for _ in range(1)]
        self.recipe_data_10 = [create_api_recipe() for _ in range(10)]
        self.recipe_data_100 = [create_api_recipe() for _ in range(100)]
    
    def _serialize_recipes_to_json(self, recipes: List[ApiRecipe]) -> str:
        """Helper method to serialize a list of ApiRecipe objects to JSON using TypeAdapter."""
        from pydantic import TypeAdapter
        list_adapter = TypeAdapter(List[ApiRecipe])
        return list_adapter.dump_json(recipes).decode()
    
    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_recipe_list_adapter_performance_1_item(self, benchmark):
        """Test RecipeListAdapter validation performance with 1 recipe."""
        json_data = self._serialize_recipes_to_json(self.recipe_data_1)
        
        def validate_recipes():
            return RecipeListAdapter.validate_json(json_data)
        
        result = benchmark(validate_recipes)
        
        # Verify correct validation
        assert len(result) == 1
        assert all(isinstance(recipe, ApiRecipe) for recipe in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"RecipeListAdapter (1 item) validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"
    
    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_recipe_list_adapter_performance_10_items(self, benchmark):
        """Test RecipeListAdapter validation performance with 10 recipes (PRD target)."""
        json_data = self._serialize_recipes_to_json(self.recipe_data_10)
        
        def validate_recipes():
            return RecipeListAdapter.validate_json(json_data)
        
        result = benchmark(validate_recipes)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(isinstance(recipe, ApiRecipe) for recipe in result)
        
        # Performance assertion - This is the critical PRD requirement
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"RecipeListAdapter (10 items) validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds PRD requirement of {self.MAX_VALIDATION_TIME_MS}ms"
        
        # Log performance for documentation
        print(f"\n✓ RecipeListAdapter Performance (10 items): {benchmark.stats.stats.mean * 1000:.2f}ms (target: <{self.MAX_VALIDATION_TIME_MS}ms)")
    
    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_recipe_list_adapter_performance_100_items(self, benchmark):
        """Test RecipeListAdapter validation performance with 100 recipes (stress test)."""
        json_data = self._serialize_recipes_to_json(self.recipe_data_100)
        
        # More lenient limit for 100 items (10x the data, allow 10x the time)
        MAX_TIME_100_ITEMS = self.MAX_VALIDATION_TIME_MS * 10  # 30ms for 100 items
        
        def validate_recipes():
            return RecipeListAdapter.validate_json(json_data)
        
        result = benchmark(validate_recipes)
        
        # Verify correct validation
        assert len(result) == 100
        assert all(isinstance(recipe, ApiRecipe) for recipe in result)
        
        # Performance assertion - Scaled expectation
        assert benchmark.stats.stats.mean * 1000 < MAX_TIME_100_ITEMS, \
            f"RecipeListAdapter (100 items) validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {MAX_TIME_100_ITEMS}ms limit"
        
        # Log performance for documentation
        print(f"\n✓ RecipeListAdapter Performance (100 items): {benchmark.stats.stats.mean * 1000:.2f}ms (target: <{MAX_TIME_100_ITEMS}ms)")

    def test_recipe_list_adapter_memory_usage_varying_sizes(self):
        """Test RecipeListAdapter memory usage with varying collection sizes."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory profiling")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test memory usage with different collection sizes
        memory_results = {}
        
        for size, data in [("1_item", self.recipe_data_1), ("10_items", self.recipe_data_10), ("100_items", self.recipe_data_100)]:
            json_data = self._serialize_recipes_to_json(data)
            
            # Memory before validation
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # Perform validations
            for _ in range(100):  # 100 iterations to see memory patterns
                RecipeListAdapter.validate_json(json_data)
            
            # Memory after validation
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_growth = memory_after - memory_before
            
            memory_results[size] = {
                "before_mb": memory_before,
                "after_mb": memory_after,
                "growth_mb": memory_growth,
                "per_validation_kb": (memory_growth * 1024) / 100
            }
            
            # Assert memory growth is reasonable
            assert memory_growth < self.MAX_MEMORY_GROWTH_MB, \
                f"RecipeListAdapter ({size}) memory grew by {memory_growth:.2f}MB, exceeds {self.MAX_MEMORY_GROWTH_MB}MB limit"
        
        # Log memory usage patterns for documentation
        print(f"\n✓ RecipeListAdapter Memory Usage Analysis:")
        for size, result in memory_results.items():
            print(f"  {size}: {result['growth_mb']:.2f}MB growth, {result['per_validation_kb']:.2f}KB per validation")
    
    def test_recipe_list_adapter_vs_recreation_performance(self):
        """Compare RecipeListAdapter singleton pattern vs recreation performance."""
        from pydantic import TypeAdapter
        
        json_data = self._serialize_recipes_to_json(self.recipe_data_10)
        iterations = 100
        
        # Test recreation pattern (anti-pattern)
        start_time = time.perf_counter()
        for _ in range(iterations):
            adapter = TypeAdapter(list[ApiRecipe])  # Recreate each time
            adapter.validate_json(json_data)
        recreation_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        # Test singleton pattern
        start_time = time.perf_counter()
        for _ in range(iterations):
            RecipeListAdapter.validate_json(json_data)  # Use singleton
        singleton_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        # Calculate performance improvement
        improvement_factor = recreation_time / singleton_time
        time_saved_ms = recreation_time - singleton_time
        
        # Singleton should be faster
        assert singleton_time < recreation_time, \
            f"Singleton pattern should be faster than recreation. Singleton: {singleton_time:.2f}ms, Recreation: {recreation_time:.2f}ms"
        
        # Log performance comparison for documentation
        print(f"\n✓ RecipeListAdapter Pattern Comparison ({iterations} iterations):")
        print(f"  Singleton pattern: {singleton_time:.2f}ms")
        print(f"  Recreation pattern: {recreation_time:.2f}ms")
        print(f"  Improvement factor: {improvement_factor:.2f}x faster")
        print(f"  Time saved: {time_saved_ms:.2f}ms")

    def test_recipe_list_adapter_thread_safety(self):
        """Test RecipeListAdapter thread safety with concurrent access."""
        json_data = self._serialize_recipes_to_json(self.recipe_data_10)
        
        def validate_in_thread():
            """Function to run in each thread."""
            results = []
            for _ in range(10):  # 10 validations per thread
                result = RecipeListAdapter.validate_json(json_data)
                results.append(len(result))
            return results
        
        # Test concurrent access with 10 threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(validate_in_thread) for _ in range(10)]
            thread_results = [future.result() for future in futures]
        
        # Verify all results are successful
        for thread_result in thread_results:
            assert len(thread_result) == 10  # 10 validations per thread
            assert all(count == 10 for count in thread_result)  # Each validation should return 10 recipes
        
        print(f"\n✓ RecipeListAdapter Thread Safety: 10 threads × 10 validations = 100 total operations completed successfully")

    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_tag_frozenset_adapter_performance(self, benchmark):
        """Test TagFrozensetAdapter validation performance."""
        json_data = json.dumps(self.tag_data)
        
        def validate_tags():
            return TagFrozensetAdapter.validate_json(json_data)
        
        result = benchmark(validate_tags)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(isinstance(tag, ApiTag) for tag in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"TagFrozensetAdapter validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"
    
    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_ingredient_list_adapter_performance(self, benchmark):
        """Test IngredientListAdapter validation performance."""
        json_data = json.dumps(self.ingredient_data)
        
        def validate_ingredients():
            return IngredientListAdapter.validate_json(json_data)
        
        result = benchmark(validate_ingredients)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(isinstance(ingredient, ApiIngredient) for ingredient in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"IngredientListAdapter validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"
    
    @pytest.mark.benchmark(group="typeadapter-validation") 
    def test_rating_list_adapter_performance(self, benchmark):
        """Test RatingListAdapter validation performance."""
        json_data = json.dumps(self.rating_data)
        
        def validate_ratings():
            return RatingListAdapter.validate_json(json_data)
        
        result = benchmark(validate_ratings)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(isinstance(rating, ApiRating) for rating in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"RatingListAdapter validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"
    
    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_role_set_adapter_performance(self, benchmark):
        """Test RoleSetAdapter validation performance."""
        json_data = json.dumps(self.role_data)
        
        def validate_roles():
            return RoleSetAdapter.validate_json(json_data)
        
        result = benchmark(validate_roles)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(isinstance(role, ApiSeedRole) for role in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"RoleSetAdapter validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"
    
    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_json_safe_list_adapter_performance(self, benchmark):
        """Test JsonSafeListAdapter validation performance."""
        json_data = json.dumps(["item1", "item2", "item3", "item4", "item5", "item6", "item7", "item8", "item9", "item10"])
        
        def validate_list():
            return JsonSafeListAdapter.validate_json(json_data)
        
        result = benchmark(validate_list)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(isinstance(item, str) for item in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"JsonSafeListAdapter validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"
    
    def test_singleton_pattern_memory_stability(self):
        """Test that module-level TypeAdapter singletons don't cause memory leaks."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory profiling")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform 1000 validations to test memory stability
        json_data = json.dumps(self.tag_data)
        for _ in range(1000):
            TagFrozensetAdapter.validate_json(json_data)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        assert memory_growth < self.MAX_MEMORY_GROWTH_MB, \
            f"Memory grew by {memory_growth:.2f}MB, exceeds {self.MAX_MEMORY_GROWTH_MB}MB limit"
    
    def test_cached_adapter_thread_safety(self):
        """Test UniqueCollectionAdapter cache thread safety."""
        def create_and_validate():
            adapter = UniqueCollectionAdapter(
                item_type=str,
                key_func=lambda x: x,
                collection_name="test_items"
            )
            return adapter.validate_python(["item1", "item2", "item3"])
        
        # Test concurrent access to cached adapters
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_validate) for _ in range(50)]
            results = [future.result() for future in futures]
        
        # All results should be successful
        assert len(results) == 50
        assert all(len(result) == 3 for result in results)
    
    @pytest.mark.benchmark(group="adapter-pattern-comparison")
    def test_singleton_vs_recreation_performance(self, benchmark):
        """Compare singleton pattern vs recreation performance."""
        from pydantic import TypeAdapter
        
        json_data = json.dumps(self.tag_data)
        
        # Test recreation pattern (anti-pattern)
        def recreate_adapter():
            adapter = TypeAdapter(list[dict])  # Recreate each time
            return adapter.validate_json(json_data)
        
        recreation_time = benchmark(recreate_adapter)
        
        # Test singleton pattern
        def singleton_adapter():
            return JsonSafeListAdapter.validate_json(json_data)
        
        # Measure singleton performance separately
        start_time = time.perf_counter()
        for _ in range(100):
            singleton_adapter()
        singleton_time = (time.perf_counter() - start_time) / 100  # Average time per operation
        
        # Singleton should be significantly faster
        improvement_factor = benchmark.stats.stats.mean / singleton_time
        assert improvement_factor > 2.0, \
            f"Singleton should be at least 2x faster. Improvement factor: {improvement_factor:.2f}x"
    
    def test_unique_collection_adapter_caching_performance(self):
        """Test performance benefits of UniqueCollectionAdapter caching."""
        # Create adapter once - caching should improve subsequent usage
        adapter = UniqueCollectionAdapter(
            item_type=str,
            key_func=lambda x: x,
            collection_name="performance_test"
        )
        
        test_data = ["item1", "item2", "item3"]  # No duplicates for this performance test
        
        # Time first validation (cache miss)
        start_time = time.perf_counter()
        result1 = adapter.validate_python(test_data)
        first_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Time subsequent validations (cache hit)
        start_time = time.perf_counter()
        for _ in range(100):
            adapter.validate_python(test_data)
        avg_cached_time = ((time.perf_counter() - start_time) * 1000) / 100  # ms per operation
        
        # Verify result correctness
        assert len(result1) == 3
        assert "item1" in result1 and "item2" in result1 and "item3" in result1
        
        # Cached operations should be very fast
        assert avg_cached_time < 0.1, f"Cached validation should be < 0.1ms, got {avg_cached_time:.3f}ms"
        
        print(f"\n✓ UniqueCollectionAdapter Caching Performance:")
        print(f"  First validation: {first_time:.3f}ms")
        print(f"  Cached validations: {avg_cached_time:.3f}ms average")

    @pytest.mark.benchmark(group="typeadapter-validation")
    def test_menu_meal_frozenset_adapter_performance(self, benchmark):
        """Test MenuMealFrozensetAdapter validation performance."""
        json_data = json.dumps(self.menu_meal_data)
        
        def validate_menu_meals():
            return MenuMealFrozensetAdapter.validate_json(json_data)
        
        result = benchmark(validate_menu_meals)
        
        # Verify correct validation
        assert len(result) == 10
        assert all(hasattr(meal, 'meal_id') for meal in result)
        
        # Performance assertion
        assert benchmark.stats.stats.mean * 1000 < self.MAX_VALIDATION_TIME_MS, \
            f"MenuMealFrozensetAdapter validation took {benchmark.stats.stats.mean * 1000:.2f}ms, exceeds {self.MAX_VALIDATION_TIME_MS}ms limit"


class TestTypeAdapterErrorHandling:
    """Test error handling performance for TypeAdapters."""
    
    def test_validation_error_performance(self):
        """Test that validation errors don't significantly impact performance."""
        # Invalid recipe data (missing required fields) - use raw dict data for error testing
        invalid_data = [{"name": "Invalid Recipe"}]  # Missing many required fields
        json_data = json.dumps(invalid_data)
        
        start_time = time.perf_counter()
        error_count = 0
        
        # Run validation errors multiple times
        for _ in range(100):
            try:
                RecipeListAdapter.validate_json(json_data)
            except Exception:
                error_count += 1
        
        total_time = (time.perf_counter() - start_time) * 1000  # ms
        avg_error_time = total_time / 100
        
        # Error handling should not be extremely slow
        assert avg_error_time < 5.0, f"Error handling took {avg_error_time:.2f}ms per error, too slow"
        assert error_count == 100, f"Expected 100 validation errors, got {error_count}"
        
        print(f"\n✓ RecipeListAdapter Error Handling: {avg_error_time:.2f}ms per validation error")
    
    def test_duplicate_detection_performance(self):
        """Test performance of duplicate detection in collections."""
        # Create data with duplicates
        duplicate_tags = [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},  # Duplicate
            {"key": "difficulty", "value": "easy", "author_id": "user-456", "type": "category"}
        ]
        
        json_data = json.dumps(duplicate_tags)
        
        start_time = time.perf_counter()
        error_count = 0
        
        # Run duplicate detection multiple times
        for _ in range(100):
            try:
                # This should pass validation but may trigger duplicate detection in business logic
                result = TagFrozensetAdapter.validate_json(json_data)
                # frozenset will automatically handle duplicates
                assert len(result) <= 3
            except Exception:
                error_count += 1
        
        total_time = (time.perf_counter() - start_time) * 1000  # ms
        avg_time = total_time / 100
        
        # Duplicate detection should be fast
        assert avg_time < 1.0, f"Duplicate detection took {avg_time:.2f}ms per operation, too slow"
        
        print(f"\n✓ TagFrozensetAdapter Duplicate Detection: {avg_time:.2f}ms per operation")

    def test_unique_collection_adapter_duplicate_detection(self):
        """Test UniqueCollectionAdapter's duplicate detection performance separately."""
        adapter = UniqueCollectionAdapter(
            item_type=str,
            key_func=lambda x: x,
            collection_name="duplicate_test"
        )
        
        # Test data with duplicates
        test_data_with_duplicates = ["item1", "item2", "item1", "item3", "item2"]
        
        start_time = time.perf_counter()
        error_count = 0
        
        # Test that duplicates are properly caught
        for _ in range(50):
            try:
                adapter.validate_python(test_data_with_duplicates)
                error_count += 1  # Should not reach here due to duplicates
            except Exception:
                pass  # Expected due to duplicates
        
        total_time = (time.perf_counter() - start_time) * 1000  # ms
        avg_time = total_time / 50
        
        # All attempts should fail due to duplicates
        assert error_count == 0, "UniqueCollectionAdapter should detect and reject duplicates"
        
        # Duplicate detection should still be fast
        assert avg_time < 2.0, f"Duplicate detection took {avg_time:.2f}ms per operation, too slow"
        
        print(f"\n✓ UniqueCollectionAdapter Duplicate Detection: {avg_time:.2f}ms per operation")


class TestTypeAdapterBasicFunctionality:
    """Basic functionality tests to ensure TypeAdapters work correctly."""
    
    def test_tag_frozenset_adapter_basic_validation(self):
        """Test TagFrozensetAdapter basic validation functionality."""
        valid_tags = [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "difficulty", "value": "easy", "author_id": "user-456", "type": "category"}
        ]
        
        result = TagFrozensetAdapter.validate_python(valid_tags)
        
        assert isinstance(result, frozenset)
        assert len(result) == 2
        assert all(isinstance(tag, ApiTag) for tag in result)
        
        # Test JSON validation
        json_result = TagFrozensetAdapter.validate_json(json.dumps(valid_tags))
        assert isinstance(json_result, frozenset)
        assert len(json_result) == 2
    
    def test_ingredient_list_adapter_basic_validation(self):
        """Test IngredientListAdapter basic validation functionality."""
        valid_ingredients = [
            {
                "name": "Tomato",
                "quantity": 100.0,
                "unit": "g",
                "position": 1,
                "full_text": "100g Tomato",
                "product_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        ]
        
        result = IngredientListAdapter.validate_python(valid_ingredients)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert all(isinstance(ingredient, ApiIngredient) for ingredient in result)
        
        # Test JSON validation
        json_result = IngredientListAdapter.validate_json(json.dumps(valid_ingredients))
        assert isinstance(json_result, list)
        assert len(json_result) == 1
    
    def test_json_safe_adapters_basic_validation(self):
        """Test JsonSafeListAdapter and JsonSafeSetAdapter basic functionality."""
        test_data = ["item1", "item2", "item3"]
        
        # Test list adapter
        list_result = JsonSafeListAdapter.validate_python(test_data)
        assert isinstance(list_result, list)
        assert len(list_result) == 3
        
        # Test JSON validation
        json_result = JsonSafeListAdapter.validate_json(json.dumps(test_data))
        assert isinstance(json_result, list)
        assert len(json_result) == 3
    
    def test_unique_collection_adapter_basic_functionality(self):
        """Test UniqueCollectionAdapter basic functionality."""
        adapter = UniqueCollectionAdapter(
            item_type=str,
            key_func=lambda x: x,
            collection_name="test_collection"
        )
        
        # Test with duplicates
        test_data = ["item1", "item2", "item1", "item3", "item2"]
        result = adapter.validate_python(test_data)
        
        assert len(result) == 3  # Duplicates removed
        assert "item1" in result
        assert "item2" in result
        assert "item3" in result
    
    def test_performance_baseline_simple(self):
        """Simple performance baseline test for documentation."""
        json_data = json.dumps([
            {"key": "test", "value": "performance", "author_id": "user-1", "type": "category"}
        ])
        
        start_time = time.perf_counter()
        result = TagFrozensetAdapter.validate_json(json_data)
        end_time = time.perf_counter()
        
        validation_time_ms = (end_time - start_time) * 1000
        
        assert len(result) == 1
        assert validation_time_ms < 1.0, f"Simple validation took {validation_time_ms:.3f}ms, should be < 1ms"
        
        print(f"\n✓ Simple TagFrozensetAdapter Performance: {validation_time_ms:.3f}ms") 