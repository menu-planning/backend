"""
ApiMeal Performance Test Suite

Performance tests for ApiMeal conversion methods and field validation.
Tests focus on behavior and performance characteristics with different data sizes
and complexity levels rather than implementation details.

Following the same pattern as test_api_meal_core.py but focused on performance.
"""

import gc
import time

from uuid import uuid4
import pytest
import psutil
import os

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Import test data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal_without_recipes,
    create_api_meal_with_max_recipes,
    create_complex_api_meal,
    create_simple_api_meal,
)


class PerformanceMetrics:
    """Helper class for capturing performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process(os.getpid())
    
    def start_measurement(self):
        """Start measuring time and memory."""
        gc.collect()  # Force garbage collection for consistent memory readings
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.perf_counter()
    
    def end_measurement(self):
        """End measuring time and memory."""
        self.end_time = time.perf_counter()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    @property
    def execution_time(self) -> float:
        """Get execution time in seconds."""
        return self.end_time - self.start_time if self.start_time and self.end_time else 0
    
    @property
    def memory_delta(self) -> float:
        """Get memory usage delta in MB."""
        return self.end_memory - self.start_memory if self.start_memory and self.end_memory else 0


class TestApiMealValidationPerformance:
    """
    Performance tests for ApiMeal field validation.
    Tests how validation performance scales with different input complexities.
    """

    @pytest.mark.parametrize("recipe_count", [1, 5, 10, 25, 50])
    def test_field_validation_performance_with_recipe_count(self, recipe_count):
        """Test how field validation performance scales with recipe count."""
        metrics = PerformanceMetrics()
        
        # Create test data with varying recipe counts
        base_meal = create_simple_api_meal()
        assert base_meal.recipes is not None
        recipes = [base_meal.recipes[0] for _ in range(recipe_count)]
        
        # Prepare meal data for validation
        meal_data = {
            "id": base_meal.id,
            "name": base_meal.name,
            "author_id": base_meal.author_id,
            "menu_id": base_meal.menu_id,
            "recipes": recipes,
            "tags": base_meal.tags,
            "description": base_meal.description,
            "notes": base_meal.notes,
            "like": base_meal.like,
            "image_url": base_meal.image_url,
            "nutri_facts": base_meal.nutri_facts,
            "weight_in_grams": base_meal.weight_in_grams,
            "calorie_density": base_meal.calorie_density,
            "carbo_percentage": base_meal.carbo_percentage,
            "protein_percentage": base_meal.protein_percentage,
            "total_fat_percentage": base_meal.total_fat_percentage,
            "created_at": base_meal.created_at,
            "updated_at": base_meal.updated_at,
            "discarded": base_meal.discarded,
            "version": base_meal.version,
        }
        
        # Measure validation performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            validated_meal = ApiMeal.model_validate(meal_data)
            assert validated_meal.recipes is not None
            assert len(validated_meal.recipes) == recipe_count
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < 1.0, f"Validation with {recipe_count} recipes should complete in <1s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 50, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"
        
        # Performance scales linearly with recipe count (allow some overhead)
        expected_max_time = 0.01 * recipe_count + 0.1  # 10ms per recipe + 100ms overhead
        assert metrics.execution_time < expected_max_time, f"Performance should scale linearly with recipe count"

    @pytest.mark.parametrize("tag_count", [0, 5, 10, 25, 50])
    def test_field_validation_performance_with_tag_count(self, tag_count):
        """Test how field validation performance scales with tag count."""
        metrics = PerformanceMetrics()

        # Create test data with varying tag counts
        author_id = str(uuid4())
        tags = [ApiTag(key=f"test={i}", value=f"value={i}", type="meal", author_id=author_id) for i in range(tag_count)]
        base_meal = create_simple_api_meal(author_id=author_id, tags=frozenset(tags))
        
        # Prepare meal data for validation
        meal_data = {
            "id": base_meal.id,
            "name": base_meal.name,
            "author_id": base_meal.author_id,
            "menu_id": base_meal.menu_id,
            "recipes": base_meal.recipes,
            "tags": base_meal.tags,
            "description": base_meal.description,
            "notes": base_meal.notes,
            "like": base_meal.like,
            "image_url": base_meal.image_url,
            "nutri_facts": base_meal.nutri_facts,
            "weight_in_grams": base_meal.weight_in_grams,
            "calorie_density": base_meal.calorie_density,
            "carbo_percentage": base_meal.carbo_percentage,
            "protein_percentage": base_meal.protein_percentage,
            "total_fat_percentage": base_meal.total_fat_percentage,
            "created_at": base_meal.created_at,
            "updated_at": base_meal.updated_at,
            "discarded": base_meal.discarded,
            "version": base_meal.version,
        }
        
        # Measure validation performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            validated_meal = ApiMeal.model_validate(meal_data)
            assert validated_meal.tags is not None
            assert len(validated_meal.tags) == tag_count
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < 0.5, f"Validation with {tag_count} tags should complete in <0.5s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 30, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"
        
        # Performance scales linearly with tag count (allow some overhead)
        expected_max_time = 0.005 * tag_count + 0.1  # 5ms per tag + 100ms overhead
        assert metrics.execution_time < expected_max_time, f"Performance should scale linearly with tag count"

    @pytest.mark.parametrize("complexity", ["simple", "medium", "complex"])
    def test_field_validation_performance_with_complexity(self, complexity):
        """Test field validation performance with different meal complexities."""
        metrics = PerformanceMetrics()
        
        # Create test data with different complexity levels
        if complexity == "simple":
            test_meal = create_simple_api_meal()
            expected_max_time = 0.1
        elif complexity == "medium":
            test_meal = create_complex_api_meal()
            expected_max_time = 0.3
        else:  # complex
            test_meal = create_api_meal_with_max_recipes()
            expected_max_time = 0.5
        
        # Prepare meal data for validation
        meal_json_data = test_meal.model_dump_json()
        
        # Measure validation performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            validated_meal = ApiMeal.model_validate_json(meal_json_data)
            assert validated_meal.name == test_meal.name
            assert validated_meal.recipes is not None
            assert test_meal.recipes is not None
            assert len(validated_meal.recipes) == len(test_meal.recipes)
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < expected_max_time, f"Validation for {complexity} meal should complete in <{expected_max_time}s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 100, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    def test_json_serialization_performance(self):
        """Test JSON serialization performance with complex meals."""
        metrics = PerformanceMetrics()
        
        # Create complex meal for testing
        complex_meal = create_api_meal_with_max_recipes()
        
        # Measure JSON serialization performance
        metrics.start_measurement()
        
        for _ in range(100):  # Run multiple times for better averaging
            json_str = complex_meal.model_dump_json()
            assert len(json_str) > 100  # Basic sanity check
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < 0.5, f"JSON serialization should complete in <0.5s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 50, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    def test_json_deserialization_performance(self):
        """Test JSON deserialization performance with complex meals."""
        metrics = PerformanceMetrics()
        
        # Create complex meal and serialize it
        complex_meal = create_api_meal_with_max_recipes()
        json_str = complex_meal.model_dump_json()
        
        # Measure JSON deserialization performance
        metrics.start_measurement()
        
        for _ in range(100):  # Run multiple times for better averaging
            restored_meal = ApiMeal.model_validate_json(json_str)
            assert restored_meal.name == complex_meal.name
            assert restored_meal.recipes is not None
            assert complex_meal.recipes is not None
            assert len(restored_meal.recipes) == len(complex_meal.recipes)
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < 1.0, f"JSON deserialization should complete in <1.0s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 100, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"


class TestApiMealConversionPerformance:
    """
    Performance tests for ApiMeal conversion methods.
    Tests the performance of from_domain, to_domain, from_orm_model, and to_orm_kwargs.
    """

    @pytest.mark.parametrize("recipe_count", [1, 5, 10, 25, 50])
    def test_from_domain_performance_with_recipe_count(self, recipe_count, domain_meal_factory):
        """Test from_domain performance with varying recipe counts."""
        metrics = PerformanceMetrics()
        
        # Create domain meal with specified recipe count
        domain_meal = domain_meal_factory(recipe_count=recipe_count)
        
        # Measure from_domain performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            api_meal = ApiMeal.from_domain(domain_meal)
            assert api_meal.recipes is not None
            assert len(api_meal.recipes) == recipe_count
            assert api_meal.name == domain_meal.name
        
        metrics.end_measurement()
        
        # Performance assertions
        expected_max_time = 0.01 * recipe_count + 0.1  # 10ms per recipe + 100ms overhead
        assert metrics.execution_time < expected_max_time, f"from_domain with {recipe_count} recipes should complete in <{expected_max_time}s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 50, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    @pytest.mark.parametrize("recipe_count", [1, 5, 10, 25, 50])
    def test_to_domain_performance_with_recipe_count(self, recipe_count):
        """Test to_domain performance with varying recipe counts."""
        metrics = PerformanceMetrics()
        
        # Create API meal with specified recipe count
        base_meal = create_simple_api_meal()
        assert base_meal.recipes is not None
        recipes = [base_meal.recipes[0] for _ in range(recipe_count)]
        
        # Create new meal instance with multiple recipes
        api_meal = ApiMeal(
            id=base_meal.id,
            name=base_meal.name,
            author_id=base_meal.author_id,
            menu_id=base_meal.menu_id,
            recipes=recipes,
            tags=base_meal.tags,
            description=base_meal.description,
            notes=base_meal.notes,
            like=base_meal.like,
            image_url=base_meal.image_url,
            nutri_facts=base_meal.nutri_facts,
            weight_in_grams=base_meal.weight_in_grams,
            calorie_density=base_meal.calorie_density,
            carbo_percentage=base_meal.carbo_percentage,
            protein_percentage=base_meal.protein_percentage,
            total_fat_percentage=base_meal.total_fat_percentage,
            created_at=base_meal.created_at,
            updated_at=base_meal.updated_at,
            discarded=base_meal.discarded,
            version=base_meal.version,
        )
        
        # Measure to_domain performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            domain_meal = api_meal.to_domain()
            assert len(domain_meal.recipes) == recipe_count
            assert domain_meal.name == api_meal.name
        
        metrics.end_measurement()
        
        # Performance assertions
        expected_max_time = 0.015 * recipe_count + 0.15  # 15ms per recipe + 150ms overhead (domain conversion is more complex)
        assert metrics.execution_time < expected_max_time, f"to_domain with {recipe_count} recipes should complete in <{expected_max_time}s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 75, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    @pytest.mark.parametrize("recipe_count", [1, 5, 10, 25, 50])
    def test_from_orm_model_performance_with_recipe_count(self, recipe_count, orm_meal_factory):
        """Test from_orm_model performance with varying recipe counts."""
        metrics = PerformanceMetrics()
        
        # Create ORM meal with specified recipe count
        orm_meal = orm_meal_factory(recipe_count=recipe_count)
        
        # Measure from_orm_model performance
        metrics.start_measurement()
        print(f'HERE: {orm_meal}')
        
        for _ in range(10):  # Run multiple times for better averaging
            api_meal = ApiMeal.from_orm_model(orm_meal)
            assert api_meal.recipes is not None
            assert len(api_meal.recipes) == recipe_count
            assert api_meal.name == orm_meal.name
        
        metrics.end_measurement()
        
        # Performance assertions
        expected_max_time = 0.012 * recipe_count + 0.12  # 12ms per recipe + 120ms overhead
        assert metrics.execution_time < expected_max_time, f"from_orm_model with {recipe_count} recipes should complete in <{expected_max_time}s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 60, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    @pytest.mark.parametrize("recipe_count", [1, 5, 10, 25, 50])
    def test_to_orm_kwargs_performance_with_recipe_count(self, recipe_count):
        """Test to_orm_kwargs performance with varying recipe counts."""
        metrics = PerformanceMetrics()
        
        # Create API meal with specified recipe count
        base_meal = create_simple_api_meal()
        assert base_meal.recipes is not None
        recipes = [base_meal.recipes[0] for _ in range(recipe_count)]
        
        # Create new meal instance with multiple recipes
        api_meal = ApiMeal(
            id=base_meal.id,
            name=base_meal.name,
            author_id=base_meal.author_id,
            menu_id=base_meal.menu_id,
            recipes=recipes,
            tags=base_meal.tags,
            description=base_meal.description,
            notes=base_meal.notes,
            like=base_meal.like,
            image_url=base_meal.image_url,
            nutri_facts=base_meal.nutri_facts,
            weight_in_grams=base_meal.weight_in_grams,
            calorie_density=base_meal.calorie_density,
            carbo_percentage=base_meal.carbo_percentage,
            protein_percentage=base_meal.protein_percentage,
            total_fat_percentage=base_meal.total_fat_percentage,
            created_at=base_meal.created_at,
            updated_at=base_meal.updated_at,
            discarded=base_meal.discarded,
            version=base_meal.version,
        )
        
        # Measure to_orm_kwargs performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            orm_kwargs = api_meal.to_orm_kwargs()
            assert len(orm_kwargs["recipes"]) == recipe_count
            assert orm_kwargs["name"] == api_meal.name
        
        metrics.end_measurement()
        
        # Performance assertions
        expected_max_time = 0.008 * recipe_count + 0.08  # 8ms per recipe + 80ms overhead
        assert metrics.execution_time < expected_max_time, f"to_orm_kwargs with {recipe_count} recipes should complete in <{expected_max_time}s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 40, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    @pytest.mark.parametrize("complexity", ["simple", "medium", "complex"])
    def test_conversion_methods_performance_by_complexity(self, complexity):
        """Test all conversion methods performance with different meal complexities."""
        metrics = PerformanceMetrics()
        
        # Create test data with different complexity levels
        if complexity == "simple":
            api_meal = create_simple_api_meal()
            expected_max_time = 0.2
        elif complexity == "medium":
            api_meal = create_complex_api_meal()
            expected_max_time = 0.5
        else:  # complex
            api_meal = create_api_meal_with_max_recipes()
            expected_max_time = 1.0
        
        # Test all conversion methods
        metrics.start_measurement()
        
        for _ in range(5):  # Run multiple times for better averaging
            # Test conversion cycle
            domain_meal = api_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Basic validation
            assert domain_meal.name == api_meal.name
            assert api_from_domain.name == api_meal.name
            assert orm_kwargs["name"] == api_meal.name
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < expected_max_time, f"Conversion cycle for {complexity} meal should complete in <{expected_max_time}s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 150, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    def test_nested_objects_conversion_performance(self):
        """Test performance of nested object conversions."""
        metrics = PerformanceMetrics()
        
        # Create meal with complex nested objects
        complex_meal = create_api_meal_with_max_recipes()
        
        # Measure nested object conversion performance
        metrics.start_measurement()
        
        for _ in range(20):  # Run multiple times for better averaging
            # Convert to domain and back (tests nested object handling)
            domain_meal = complex_meal.to_domain()
            api_meal = ApiMeal.from_domain(domain_meal)
            
            # Verify nested objects are properly converted
            assert api_meal.recipes is not None
            assert api_meal.tags is not None
            assert complex_meal.recipes is not None
            assert complex_meal.tags is not None
            assert len(api_meal.recipes) == len(complex_meal.recipes)
            assert len(api_meal.tags) == len(complex_meal.tags)
            if api_meal.nutri_facts and complex_meal.nutri_facts:
                assert api_meal.nutri_facts.calories.value == complex_meal.nutri_facts.calories.value
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < 1.0, f"Nested object conversion should complete in <1.0s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 100, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"

    def test_computed_properties_performance(self):
        """Test performance of computed properties calculation during conversion."""
        metrics = PerformanceMetrics()
        
        # Create meal with recipes that will trigger computed properties calculation
        complex_meal = create_api_meal_with_max_recipes()
        
        # Measure computed properties calculation performance
        metrics.start_measurement()
        
        for _ in range(10):  # Run multiple times for better averaging
            # Domain conversion triggers computed properties calculation
            domain_meal = complex_meal.to_domain()
            api_meal = ApiMeal.from_domain(domain_meal)
            
            # Verify computed properties are calculated
            assert api_meal.weight_in_grams is not None
            if api_meal.nutri_facts:
                assert api_meal.nutri_facts.calories.value > 0
                assert api_meal.calorie_density is not None
        
        metrics.end_measurement()
        
        # Performance assertions
        assert metrics.execution_time < 0.5, f"Computed properties calculation should complete in <0.5s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 50, f"Memory usage should be reasonable, used {metrics.memory_delta:.2f}MB"


class TestApiMealMemoryPerformance:
    """
    Performance tests focused on memory usage patterns.
    Tests memory efficiency during different operations.
    """

    def test_memory_usage_with_increasing_recipe_count(self):
        """Test memory usage patterns with increasing recipe counts."""
        base_meal = create_simple_api_meal()
        assert base_meal.recipes is not None
        base_recipe = base_meal.recipes[0]
        
        memory_usage_data = []
        
        for recipe_count in [1, 5, 10, 25, 50, 100]:
            metrics = PerformanceMetrics()
            
            # Create meal with specified recipe count
            recipes = [base_recipe for _ in range(recipe_count)]
            
            metrics.start_measurement()
            
            # Create API meal
            api_meal = ApiMeal(
                id=base_meal.id,
                name=base_meal.name,
                author_id=base_meal.author_id,
                menu_id=base_meal.menu_id,
                recipes=recipes,
                tags=base_meal.tags,
                description=base_meal.description,
                notes=base_meal.notes,
                like=base_meal.like,
                image_url=base_meal.image_url,
                nutri_facts=base_meal.nutri_facts,
                weight_in_grams=base_meal.weight_in_grams,
                calorie_density=base_meal.calorie_density,
                carbo_percentage=base_meal.carbo_percentage,
                protein_percentage=base_meal.protein_percentage,
                total_fat_percentage=base_meal.total_fat_percentage,
                created_at=base_meal.created_at,
                updated_at=base_meal.updated_at,
                discarded=base_meal.discarded,
                version=base_meal.version,
            )
            
            # Perform conversion operations
            domain_meal = api_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            metrics.end_measurement()
            
            memory_usage_data.append({
                'recipe_count': recipe_count,
                'memory_delta': metrics.memory_delta,
                'execution_time': metrics.execution_time
            })
            
            # Basic assertions
            assert api_meal.recipes is not None
            assert len(api_meal.recipes) == recipe_count
            assert len(domain_meal.recipes) == recipe_count
            assert len(orm_kwargs["recipes"]) == recipe_count
        
        # Analyze memory usage pattern
        for i in range(1, len(memory_usage_data)):
            prev_data = memory_usage_data[i-1]
            curr_data = memory_usage_data[i]
            
            # Memory usage should scale reasonably with recipe count
            memory_growth_ratio = curr_data['memory_delta'] / max(prev_data['memory_delta'], 1)
            recipe_growth_ratio = curr_data['recipe_count'] / prev_data['recipe_count']
            
            # Memory growth should not exceed 3x the recipe growth ratio
            assert memory_growth_ratio < recipe_growth_ratio * 3, \
                f"Memory usage growing too fast: {memory_growth_ratio:.2f}x vs recipe growth {recipe_growth_ratio:.2f}x"

    def test_memory_efficiency_during_round_trip_conversions(self):
        """Test memory efficiency during multiple round-trip conversions."""
        metrics = PerformanceMetrics()
        
        # Create complex meal for testing
        complex_meal = create_api_meal_with_max_recipes()
        
        metrics.start_measurement()
        
        # Perform multiple round-trip conversions
        for _ in range(10):
            # API → Domain → API
            domain_meal = complex_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            
            # API → ORM kwargs
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Verify data integrity
            assert api_from_domain.name == complex_meal.name
            assert api_from_domain.recipes is not None
            assert complex_meal.recipes is not None
            assert len(api_from_domain.recipes) == len(complex_meal.recipes)
            assert orm_kwargs["name"] == complex_meal.name
        
        metrics.end_measurement()
        
        # Memory usage should be reasonable for multiple conversions
        assert metrics.memory_delta < 200, f"Memory usage during round-trip conversions should be <200MB, used {metrics.memory_delta:.2f}MB"
        assert metrics.execution_time < 2.0, f"Round-trip conversions should complete in <2.0s, took {metrics.execution_time:.3f}s"

    def test_memory_cleanup_after_operations(self):
        """Test that memory is properly cleaned up after operations."""
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        for _ in range(20):
            # Create large meal
            large_meal = create_api_meal_with_max_recipes()
            
            # Perform conversions
            domain_meal = large_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Delete references to force cleanup
            del large_meal, domain_meal, api_from_domain, orm_kwargs
        
        # Force garbage collection
        gc.collect()
        
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal after cleanup
        assert memory_growth < 50, f"Memory growth after cleanup should be <50MB, grew {memory_growth:.2f}MB"


class TestApiMealEdgeCasePerformance:
    """
    Performance tests for edge cases and boundary conditions.
    """

    def test_empty_collections_performance(self):
        """Test performance with empty collections."""
        metrics = PerformanceMetrics()
        
        # Create meal with empty collections
        empty_meal = create_api_meal_without_recipes(tags=frozenset())
        
        metrics.start_measurement()
        
        for _ in range(100):  # Run many times since empty collections should be fast
            # Test all conversion methods with empty collections
            domain_meal = empty_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Verify empty collections are handled correctly
            assert api_from_domain.recipes is not None
            assert api_from_domain.tags is not None
            assert len(api_from_domain.recipes) == 0
            assert len(api_from_domain.tags) == 0
            assert len(orm_kwargs["recipes"]) == 0
            assert len(orm_kwargs["tags"]) == 0
        
        metrics.end_measurement()
        
        # Empty collections should be very fast
        assert metrics.execution_time < 0.2, f"Empty collections should be very fast, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 10, f"Empty collections should use minimal memory, used {metrics.memory_delta:.2f}MB"

    def test_maximum_collections_performance(self):
        """Test performance with maximum-sized collections."""
        metrics = PerformanceMetrics()
        
        # Create meal with maximum collections
        max_meal = create_api_meal_with_max_recipes()
        
        metrics.start_measurement()
        
        for _ in range(5):  # Run fewer times since max collections are heavy
            # Test all conversion methods with maximum collections
            domain_meal = max_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Verify maximum collections are handled correctly
            assert api_from_domain.recipes is not None
            assert api_from_domain.tags is not None
            assert max_meal.recipes is not None
            assert max_meal.tags is not None
            assert len(api_from_domain.recipes) == len(max_meal.recipes)
            assert len(api_from_domain.tags) == len(max_meal.tags)
            assert len(orm_kwargs["recipes"]) == len(max_meal.recipes)
            assert len(orm_kwargs["tags"]) == len(max_meal.tags)
        
        metrics.end_measurement()
        
        # Maximum collections should still be reasonably fast
        assert metrics.execution_time < 2.0, f"Maximum collections should complete in <2.0s, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 200, f"Maximum collections should use reasonable memory, used {metrics.memory_delta:.2f}MB"

    def test_null_optional_fields_performance(self):
        """Test performance with null optional fields."""
        metrics = PerformanceMetrics()
        
        # Create meal with minimal data (most optional fields null)
        minimal_meal = create_simple_api_meal(
            menu_id=None,
            description=None,
            notes=None,
            like=None,
            image_url=None,
            recipes=[],
        )
               
        metrics.start_measurement()
        
        for _ in range(50):  # Run many times since null fields should be fast
            # Test all conversion methods with null fields
            domain_meal = minimal_meal.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Verify null fields are handled correctly
            assert api_from_domain.name == minimal_meal.name
            assert orm_kwargs["name"] == minimal_meal.name
        
        metrics.end_measurement()
        
        # Null fields should be fast to process
        assert metrics.execution_time < 0.3, f"Null fields should be fast, took {metrics.execution_time:.3f}s"
        assert metrics.memory_delta < 20, f"Null fields should use minimal memory, used {metrics.memory_delta:.2f}MB"

    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations simulation."""
        import threading
        import queue
        
        # Create test data
        test_meals = [
            create_simple_api_meal(),
            create_complex_api_meal(),
            create_api_meal_with_max_recipes()
        ]
        
        results_queue = queue.Queue()
        
        def conversion_worker(meal_data):
            """Worker function to perform conversions."""
            start_time = time.perf_counter()
            
            # Perform conversion operations
            domain_meal = meal_data.to_domain()
            api_from_domain = ApiMeal.from_domain(domain_meal)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            results_queue.put({
                'execution_time': execution_time,
                'success': True,
                'meal_name': meal_data.name,
                'recipes_count': len(meal_data.recipes)
            })
        
        # Start multiple threads
        threads = []
        for _ in range(10):  # 10 concurrent operations
            for meal in test_meals:
                thread = threading.Thread(target=conversion_worker, args=(meal,))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify all operations completed successfully
        assert len(results) == 30  # 10 threads × 3 meals
        assert all(result['success'] for result in results)
        
        # Performance should be reasonable even under concurrent load
        max_execution_time = max(result['execution_time'] for result in results)
        avg_execution_time = sum(result['execution_time'] for result in results) / len(results)
        
        assert max_execution_time < 2.0, f"Max execution time under concurrent load should be <2.0s, was {max_execution_time:.3f}s"
        assert avg_execution_time < 0.5, f"Average execution time under concurrent load should be <0.5s, was {avg_execution_time:.3f}s"


@pytest.fixture
def domain_meal_factory():
    """Factory for creating domain meals with specified parameters."""
    def _create_domain_meal(recipe_count=3):
        # This would need to be implemented based on your domain meal creation logic
        # For now, create via API meal and convert to domain
        base_meal = create_simple_api_meal()
        assert base_meal.recipes is not None
        base_recipe = base_meal.recipes[0]
        recipes = [base_recipe for _ in range(recipe_count)]
        
        api_meal = ApiMeal(
            id=base_meal.id,
            name=base_meal.name,
            author_id=base_meal.author_id,
            menu_id=base_meal.menu_id,
            recipes=recipes,
            tags=base_meal.tags,
            description=base_meal.description,
            notes=base_meal.notes,
            like=base_meal.like,
            image_url=base_meal.image_url,
            nutri_facts=base_meal.nutri_facts,
            weight_in_grams=base_meal.weight_in_grams,
            calorie_density=base_meal.calorie_density,
            carbo_percentage=base_meal.carbo_percentage,
            protein_percentage=base_meal.protein_percentage,
            total_fat_percentage=base_meal.total_fat_percentage,
            created_at=base_meal.created_at,
            updated_at=base_meal.updated_at,
            discarded=base_meal.discarded,
            version=base_meal.version,
        )
        
        return api_meal.to_domain()
    
    return _create_domain_meal


@pytest.fixture
def orm_meal_factory():
    """Factory for creating ORM meals with specified parameters."""
    def _create_orm_meal(recipe_count=3):
        # This would need to be implemented based on your ORM meal creation logic
        # For now, create via API meal and convert to ORM kwargs, then mock ORM model
        base_meal = create_simple_api_meal()
        assert base_meal.recipes is not None
        base_recipe = base_meal.recipes[0]
        recipes = [base_recipe for _ in range(recipe_count)]
        
        api_meal = ApiMeal(
            id=base_meal.id,
            name=base_meal.name,
            author_id=base_meal.author_id,
            menu_id=base_meal.menu_id,
            recipes=recipes,
            tags=base_meal.tags,
            description=base_meal.description,
            notes=base_meal.notes,
            like=base_meal.like,
            image_url=base_meal.image_url,
            nutri_facts=base_meal.nutri_facts,
            weight_in_grams=base_meal.weight_in_grams,
            calorie_density=base_meal.calorie_density,
            carbo_percentage=base_meal.carbo_percentage,
            protein_percentage=base_meal.protein_percentage,
            total_fat_percentage=base_meal.total_fat_percentage,
            created_at=base_meal.created_at,
            updated_at=base_meal.updated_at,
            discarded=base_meal.discarded,
            version=base_meal.version,
        )
        
        # Helper function to recursively convert dicts to mock objects
        def dict_to_mock_object(data):
            if isinstance(data, dict):
                mock_obj = MockOrmObject()
                for key, value in data.items():
                    setattr(mock_obj, key, dict_to_mock_object(value))
                return mock_obj
            elif isinstance(data, list):
                return [dict_to_mock_object(item) for item in data]
            else:
                return data
        
        # Create mock ORM models for nested objects
        class MockOrmObject:
            def __init__(self):
                pass
        
        class MockOrmMeal:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    if key in ['recipes', 'tags']:
                        # Convert nested dicts to mock objects recursively
                        setattr(self, key, dict_to_mock_object(value))
                    else:
                        setattr(self, key, value)
        
        orm_kwargs = api_meal.to_orm_kwargs()
        return MockOrmMeal(**orm_kwargs)
    
    return _create_orm_meal
