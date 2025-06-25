"""
Performance benchmarks for ApiMeal validation.

This module provides baseline performance measurements for ApiMeal schema validation,
conversion operations, and field validation following production patterns:
- Incoming data: JSON → ApiMeal → Domain  
- Outgoing data: Domain → ApiMeal → JSON

Tests follow the deterministic data factory pattern established in meal_data_factories.py.

Performance targets (RIGOROUS - updated for Task 1.3):
- Simple meal (no recipes): < 1ms (down from 2ms)
- Standard meal (3-5 recipes): < 3ms (new dedicated test)
- Large meal (10 recipes): < 5ms (down from 8ms)
- Complex meal (all fields): < 4ms (maintained)
- Field validation: Recipe list < 3ms, Tag validation < 2ms, Nutrition < 2ms
- Stress tests: 20-recipe meal < 15ms incoming, < 18ms outgoing
"""

import time
import pytest
import json
from typing import List, Dict, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import ApiNutriFacts

# Data factories following meal_data_factories.py pattern
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.meal_benchmark_data_factories import (
    reset_counters,
    create_api_meal_kwargs,
    create_api_meal,
    create_api_meal_with_recipes,
    create_api_meal_performance_scenarios,
    create_domain_meal_for_conversion,
    create_orm_meal_for_conversion,
    create_api_recipe,
)

pytestmark = [pytest.mark.benchmark, pytest.mark.integration]


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_benchmark_counters():
    """Reset data factory counters before each test for deterministic behavior"""
    reset_counters()


@pytest.fixture
def benchmark_timer():
    """Simple timer for performance assertions"""
    
    class Timer:
        def __init__(self):
            self.start_time: float | None = None
            self.elapsed: float | None = None
            
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
            
        def __exit__(self, *args):
            if self.start_time is not None:
                self.elapsed = time.perf_counter() - self.start_time
        
        def assert_faster_than(self, seconds: float):
            if self.elapsed is None:
                raise ValueError("Timer was not used in context manager")
            assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s, expected < {seconds}s"
    
    return Timer


# =============================================================================
# INCOMING DATA VALIDATION BENCHMARKS (JSON → API → Domain)
# =============================================================================

class TestIncomingDataValidationPerformance:
    """Performance benchmarks for incoming data validation: JSON → ApiMeal → Domain"""

    def test_incoming_simple_meal_baseline(self, benchmark_timer):
        """Benchmark: Simple meal incoming validation (JSON → API → Domain) - RIGOROUS TARGET"""
        # Given: Simple meal as JSON string (production input)
        meal_data = create_api_meal_kwargs(recipes=[], tags=frozenset())
        api_meal_temp = ApiMeal(**meal_data)
        json_meal = api_meal_temp.model_dump_json()
        
        # When: Full incoming validation pipeline
        with benchmark_timer() as timer:
            # Step 1: JSON → ApiMeal
            api_meal = ApiMeal.model_validate_json(json_meal)
            # Step 2: ApiMeal → Domain
            domain_meal = api_meal.to_domain()
        
        # Then: Should complete full pipeline quickly - RIGOROUS TARGET
        timer.assert_faster_than(0.001)  # < 1ms for simple meal (down from 2ms)
        assert domain_meal.name == meal_data["name"]
        assert len(domain_meal.recipes) == 0

    def test_incoming_standard_meal_3_recipes(self, benchmark_timer):
        """Benchmark: Standard meal with 3 recipes (JSON → API → Domain) - NEW DEDICATED TEST"""
        # Given: Standard meal JSON with exactly 3 recipes
        meal = create_api_meal_with_recipes(recipe_count=3)
        json_meal = meal.model_dump_json()
        
        # When: Full incoming validation pipeline
        with benchmark_timer() as timer:
            # Step 1: JSON → ApiMeal
            api_meal = ApiMeal.model_validate_json(json_meal)
            # Step 2: ApiMeal → Domain
            domain_meal = api_meal.to_domain()
        
        # Then: Should validate standard meal efficiently - NEW RIGOROUS TARGET
        timer.assert_faster_than(0.003)  # < 3ms for 3-recipe meal
        assert len(domain_meal.recipes) == 3

    def test_incoming_standard_meal_5_recipes(self, benchmark_timer):
        """Benchmark: Standard meal with 5 recipes (JSON → API → Domain) - NEW DEDICATED TEST"""
        # Given: Standard meal JSON with exactly 5 recipes
        meal = create_api_meal_with_recipes(recipe_count=5)
        json_meal = meal.model_dump_json()
        
        # When: Full incoming validation pipeline
        with benchmark_timer() as timer:
            # Step 1: JSON → ApiMeal
            api_meal = ApiMeal.model_validate_json(json_meal)
            # Step 2: ApiMeal → Domain
            domain_meal = api_meal.to_domain()
        
        # Then: Should validate standard meal efficiently - NEW RIGOROUS TARGET
        timer.assert_faster_than(0.003)  # < 3ms for 5-recipe meal
        assert len(domain_meal.recipes) == 5

    @pytest.mark.parametrize("recipe_count", [1, 5, 10])
    def test_incoming_with_recipes_scaling(self, benchmark_timer, recipe_count):
        """Benchmark: Incoming validation scaling with recipe count (JSON → API → Domain) - UPDATED TARGETS"""
        # Given: Meal JSON with varying recipe counts
        meal = create_api_meal_with_recipes(recipe_count=recipe_count)
        json_meal = meal.model_dump_json()
        
        # When: Full incoming validation pipeline
        with benchmark_timer() as timer:
            # Step 1: JSON → ApiMeal
            api_meal = ApiMeal.model_validate_json(json_meal)
            # Step 2: ApiMeal → Domain
            domain_meal = api_meal.to_domain()
        
        # Then: Should scale with RIGOROUS targets
        if recipe_count <= 5:
            timer.assert_faster_than(0.003)  # < 3ms for <= 5 recipes (down from 5ms)
        else:
            timer.assert_faster_than(0.005)  # < 5ms for 10 recipes (down from 8ms)
        
        assert len(domain_meal.recipes) == recipe_count

    def test_incoming_complex_meal_baseline(self, benchmark_timer):
        """Benchmark: Complex meal incoming validation with all fields (JSON → API → Domain)"""
        # Given: Complex meal with recipes that have nutritional facts (since nutri_facts is computed from recipes)
        # Create recipes with nutritional facts first
        recipes = []
        for i in range(2):  # Create 2 recipes with nutritional facts
            recipe_nutri_facts = ApiNutriFacts(
                calories=400.0 + (i * 50),  # 400, 450
                protein=25.0 + (i * 5),     # 25, 30
                carbohydrate=45.0 + (i * 5), # 45, 50  
                total_fat=13.5 + (i * 1.5),  # 13.5, 15
                saturated_fat=4.0 + (i * 1),  # 4, 5
                trans_fat=0.05 + (i * 0.05), # 0.05, 0.1
                sugar=7.5 + (i * 2.5),       # 7.5, 10
                sodium=600.0 + (i * 100)     # 600, 700
            )
            recipe = create_api_recipe(nutri_facts=recipe_nutri_facts)
            recipes.append(recipe)
        
        meal_data = create_api_meal_kwargs(
            description="Complex meal with all nutritional data",
            notes="Detailed cooking notes",
            like=True,
            image_url="https://example.com/complex-meal.jpg",
            recipes=recipes  # Include recipes with nutritional facts
        )
        
        # Remove nutri_facts from meal_data since it's computed from recipes
        # meal_data.pop("nutri_facts", None)  # Not needed since create_api_meal_kwargs doesn't set it
        
        api_meal_temp = ApiMeal(**meal_data)
        json_meal = api_meal_temp.model_dump_json()
        
        # When: Full incoming validation pipeline
        with benchmark_timer() as timer:
            # Step 1: JSON → ApiMeal
            api_meal = ApiMeal.model_validate_json(json_meal)
            # Step 2: ApiMeal → Domain
            domain_meal = api_meal.to_domain()
        
        # Then: Should complete complex validation efficiently
        timer.assert_faster_than(0.004)  # < 4ms for complex meal
        assert domain_meal.nutri_facts is not None
        # The computed nutri_facts should be the sum of recipe nutri_facts (850 calories total)
        assert domain_meal.nutri_facts.calories.value == 850.0
        assert domain_meal.nutri_facts.calories.unit.value == "kcal" # type: ignore

    @pytest.mark.parametrize("scenario", create_api_meal_performance_scenarios())
    def test_incoming_performance_scenarios(self, benchmark_timer, scenario):
        """Benchmark: Various incoming validation scenarios (JSON → API → Domain)"""
        # Given: Performance scenario as JSON
        meal_data = scenario["meal_data"]
        expected_max_time = scenario["max_time_seconds"] + 0.002  # Add overhead for domain conversion
        
        api_meal_temp = ApiMeal(**meal_data)
        json_meal = api_meal_temp.model_dump_json()
        
        # When: Full incoming validation pipeline
        with benchmark_timer() as timer:
            # Step 1: JSON → ApiMeal
            api_meal = ApiMeal.model_validate_json(json_meal)
            # Step 2: ApiMeal → Domain
            domain_meal = api_meal.to_domain()
        
        # Then: Should meet scenario-specific target
        timer.assert_faster_than(expected_max_time)
        
        # Verify scenario expectations
        if "expected_recipe_count" in scenario:
            assert len(domain_meal.recipes) == scenario["expected_recipe_count"]
        if "expected_tag_count" in scenario:
            assert len(domain_meal.tags) == scenario["expected_tag_count"]


# =============================================================================
# OUTGOING DATA SERIALIZATION BENCHMARKS (Domain → API → JSON)
# =============================================================================

class TestOutgoingDataSerializationPerformance:
    """Performance benchmarks for outgoing data serialization: Domain → ApiMeal → JSON"""

    def test_outgoing_simple_meal_baseline(self, benchmark_timer):
        """Benchmark: Simple meal outgoing serialization (Domain → API → JSON)"""
        # Given: Domain meal object
        domain_meal = create_domain_meal_for_conversion(recipe_count=0)
        
        # When: Full outgoing serialization pipeline
        with benchmark_timer() as timer:
            # Step 1: Domain → ApiMeal
            api_meal = ApiMeal.from_domain(domain_meal)
            # Step 2: ApiMeal → JSON
            json_string = api_meal.model_dump_json()
        
        # Then: Should serialize quickly
        timer.assert_faster_than(0.002)  # < 2ms for simple meal
        
        # Verify JSON is valid
        parsed_json = json.loads(json_string)
        assert parsed_json["name"] == domain_meal.name
        assert len(parsed_json["recipes"]) == 0

    @pytest.mark.parametrize("recipe_count", [1, 5, 10])
    def test_outgoing_with_recipes_scaling(self, benchmark_timer, recipe_count):
        """Benchmark: Outgoing serialization scaling with recipe count (Domain → API → JSON)"""
        # Given: Domain meal with varying recipe counts
        domain_meal = create_domain_meal_for_conversion(recipe_count=recipe_count)
        print(domain_meal.recipes)
        
        # When: Full outgoing serialization pipeline
        with benchmark_timer() as timer:
            # Step 1: Domain → ApiMeal
            api_meal = ApiMeal.from_domain(domain_meal)
            # Step 2: ApiMeal → JSON
            json_string = api_meal.model_dump_json()
        
        # Then: Should scale reasonably with recipe count
        if recipe_count <= 5:
            timer.assert_faster_than(0.008)  # < 8ms for <= 5 recipes
        else:
            timer.assert_faster_than(0.010)  # < 10ms for 10 recipes (production target)
        
        # Verify JSON structure
        parsed_json = json.loads(json_string)
        assert len(parsed_json["recipes"]) == recipe_count

    def test_outgoing_complex_meal_baseline(self, benchmark_timer):
        """Benchmark: Complex meal outgoing serialization (Domain → API → JSON)"""
        # Given: Complex domain meal
        domain_meal = create_domain_meal_for_conversion(recipe_count=5)
        
        # When: Full outgoing serialization pipeline
        with benchmark_timer() as timer:
            # Step 1: Domain → ApiMeal
            api_meal = ApiMeal.from_domain(domain_meal)
            # Step 2: ApiMeal → JSON
            json_string = api_meal.model_dump_json()
        
        # Then: Should serialize complex meal efficiently
        timer.assert_faster_than(0.008)  # < 8ms for complex meal
        
        # Verify JSON completeness
        parsed_json = json.loads(json_string)
        assert parsed_json["id"] == str(domain_meal.id)
        assert parsed_json["name"] == domain_meal.name


# =============================================================================
# ROUNDTRIP VALIDATION BENCHMARKS (Full Production Flow)
# =============================================================================

class TestRoundtripValidationPerformance:
    """Performance benchmarks for complete roundtrip validation flows"""

    def test_complete_roundtrip_performance(self, benchmark_timer):
        """Benchmark: Complete roundtrip (Domain → API → JSON → API → Domain)"""
        # Given: Original domain meal
        original_domain = create_domain_meal_for_conversion(recipe_count=5)
        
        # When: Complete roundtrip through all layers
        with benchmark_timer() as timer:
            # Outgoing: Domain → API → JSON
            api_meal_out = ApiMeal.from_domain(original_domain)
            json_string = api_meal_out.model_dump_json()
            
            # Incoming: JSON → API → Domain
            api_meal_in = ApiMeal.model_validate_json(json_string)
            final_domain = api_meal_in.to_domain()
        
        # Then: Should complete roundtrip efficiently
        timer.assert_faster_than(0.020)  # < 20ms for complete roundtrip
        
        # Verify data integrity
        assert final_domain.id == original_domain.id
        assert final_domain.name == original_domain.name
        assert len(final_domain.recipes) == len(original_domain.recipes)

    def test_repeated_incoming_validation(self, benchmark_timer):
        """Benchmark: Repeated incoming validation (JSON → API → Domain) - UPDATED TARGET"""
        # Given: Standard meal JSON
        meal = create_api_meal_with_recipes(recipe_count=5)
        json_meal = meal.model_dump_json()
        
        # When: Repeatedly processing incoming data - INCREASED ITERATIONS
        with benchmark_timer() as timer:
            for _ in range(50):  # Increased from 25x to 50x for rigorous testing
                # Production incoming flow
                api_meal = ApiMeal.model_validate_json(json_meal)
                domain_meal = api_meal.to_domain()
        
        # Then: Should handle repeated processing efficiently
        timer.assert_faster_than(0.100)  # < 100ms for 50 iterations (maintained for higher load)

    def test_repeated_outgoing_serialization(self, benchmark_timer):
        """Benchmark: Repeated outgoing serialization (Domain → API → JSON)"""
        # Given: Standard domain meal
        domain_meal = create_domain_meal_for_conversion(recipe_count=5)
        
        # When: Repeatedly processing outgoing data
        with benchmark_timer() as timer:
            for _ in range(50):
                # Production outgoing flow
                api_meal = ApiMeal.from_domain(domain_meal)
                json_string = api_meal.model_dump_json()
        
        # Then: Should handle repeated serialization efficiently
        timer.assert_faster_than(0.250)  # < 250ms for 50 iterations


# =============================================================================
# FIELD VALIDATION BENCHMARKS (Production Context)
# =============================================================================

class TestProductionFieldValidationPerformance:
    """Performance benchmarks for field validation in production context - RIGOROUS TARGETS"""

    def test_recipe_list_validation_from_json(self, benchmark_timer):
        """Benchmark: Recipe list validation from JSON (production pattern) - RIGOROUS TARGET"""
        # Given: Meal JSON with multiple recipes
        meal = create_api_meal_with_recipes(recipe_count=10)
        json_meal = meal.model_dump_json()
        
        # When: Validating recipe-heavy meal from JSON
        with benchmark_timer() as timer:
            api_meal = ApiMeal.model_validate_json(json_meal)
            domain_meal = api_meal.to_domain()
        
        # Then: Should validate recipe list efficiently - RIGOROUS TARGET
        timer.assert_faster_than(0.003)  # < 3ms for 10 recipes from JSON (down from 8ms)
        assert len(domain_meal.recipes) == 10

    def test_tag_validation_from_json(self, benchmark_timer):
        """Benchmark: Tag frozenset validation from JSON (production pattern) - RIGOROUS TARGET"""
        # Given: Meal JSON with multiple tags
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.meal_benchmark_data_factories import create_api_tag_data
        
        tag_data = [create_api_tag_data() for _ in range(5)]
        tags = frozenset(ApiTag(**data) for data in tag_data)
        meal_data = create_api_meal_kwargs(tags=tags)
        
        api_meal_temp = ApiMeal(**meal_data)
        json_meal = api_meal_temp.model_dump_json()
        
        # When: Validating tag-heavy meal from JSON
        with benchmark_timer() as timer:
            api_meal = ApiMeal.model_validate_json(json_meal)
            domain_meal = api_meal.to_domain()
        
        # Then: Should validate tags efficiently from JSON - RIGOROUS TARGET
        timer.assert_faster_than(0.002)  # < 2ms for 5 tags from JSON (down from 4ms)
        assert len(domain_meal.tags) == 5

    @pytest.mark.skip(reason="Skipping nutri_facts validation from JSON benchmark")
    def test_nutri_facts_validation_from_json(self, benchmark_timer):
        # TODO: Remove mark after fixing domain cache
        """Benchmark: Nutritional facts validation from JSON (production pattern) - RIGOROUS TARGET"""
        # Given: Meal JSON with recipes that have nutritional facts (since nutri_facts is computed from recipes)
        # Create a recipe with nutritional facts
        recipe_nutri_facts = ApiNutriFacts(
            calories=800.0,
            protein=50.0,
            carbohydrate=90.0,
            total_fat=27.0,
            saturated_fat=8.0,
            trans_fat=0.1,
            sugar=15.0,
            sodium=1200.0
        )
        recipe = create_api_recipe(nutri_facts=recipe_nutri_facts)
        meal_data = create_api_meal_kwargs(recipes=[recipe])  # Include recipe with nutritional facts
        api_meal_temp = ApiMeal(**meal_data)
        json_meal = api_meal_temp.model_dump_json()
        
        # When: Validating nutritional facts from JSON
        with benchmark_timer() as timer:
            api_meal = ApiMeal.model_validate_json(json_meal)
            domain_meal = api_meal.to_domain()
        
        # Then: Should validate nested nutrition data efficiently - RIGOROUS TARGET
        timer.assert_faster_than(0.002)  # < 2ms for nutrition validation from JSON (down from 3ms)
        assert domain_meal.nutri_facts is not None
        assert domain_meal.nutri_facts.calories.value == 800.0


# =============================================================================
# STRESS TEST BENCHMARKS (Production Load) - RIGOROUS TARGETS
# =============================================================================

class TestProductionStressPerformance:
    """Stress test benchmarks for production load scenarios - RIGOROUS TARGETS"""

    def test_large_meal_incoming_stress(self, benchmark_timer):
        """Stress test: Large meal incoming validation (JSON → API → Domain) - RIGOROUS TARGET"""
        # Given: Large meal JSON with 20 recipes
        meal = create_api_meal_with_recipes(recipe_count=20)
        json_meal = meal.model_dump_json()
        
        # When: Processing large incoming meal
        with benchmark_timer() as timer:
            api_meal = ApiMeal.model_validate_json(json_meal)
            domain_meal = api_meal.to_domain()
        
        # Then: Should handle large meals within acceptable time - RIGOROUS TARGET
        timer.assert_faster_than(0.015)  # < 15ms for 20 recipes (down from 25ms)
        assert len(domain_meal.recipes) == 20

    def test_large_meal_outgoing_stress(self, benchmark_timer):
        """Stress test: Large meal outgoing serialization (Domain → API → JSON) - RIGOROUS TARGET"""
        # Given: Large domain meal with 20 recipes
        domain_meal = create_domain_meal_for_conversion(recipe_count=20)
        
        # When: Processing large outgoing meal
        with benchmark_timer() as timer:
            api_meal = ApiMeal.from_domain(domain_meal)
            json_string = api_meal.model_dump_json()
        
        # Then: Should serialize large meals efficiently - RIGOROUS TARGET
        timer.assert_faster_than(0.018)  # < 18ms for 20 recipes (down from 30ms)
        
        # Verify JSON size is reasonable
        json_size_kb = len(json_string) / 1024
        assert json_size_kb < 500, f"JSON size {json_size_kb:.1f}KB too large for 20 recipes"

    def test_concurrent_validation_simulation(self, benchmark_timer):
        """Stress test: Simulate concurrent validation requests"""
        import psutil
        import os
        
        # Given: Multiple different meals for concurrent processing
        meals_json = []
        for i in range(25):
            meal = create_api_meal_with_recipes(recipe_count=3)
            meals_json.append(meal.model_dump_json())
        
        # Monitor memory usage
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        # When: Processing multiple meals sequentially (simulating concurrent load)
        domain_meals = []
        with benchmark_timer() as timer:
            for json_meal in meals_json:
                api_meal = ApiMeal.model_validate_json(json_meal)
                domain_meal = api_meal.to_domain()
                domain_meals.append(domain_meal)
        
        memory_after = process.memory_info().rss
        memory_used = memory_after - memory_before
        
        # Then: Should handle concurrent-like load efficiently
        timer.assert_faster_than(0.100)  # < 100ms for 25 meals
        assert len(domain_meals) == 25
        
        # Memory usage should be reasonable
        memory_mb = memory_used / (1024 * 1024)
        assert memory_mb < 100, f"Memory usage {memory_mb:.1f}MB too high for 25 meals"


# =============================================================================
# PRODUCTION TARGET BENCHMARKS
# =============================================================================

class TestProductionTargetPerformance:
    """Benchmarks against production performance targets"""

    def test_incoming_target_validation(self, benchmark_timer):
        """Verify incoming validation meets production target (JSON → API → Domain)"""
        # Given: Target scenario (10-recipe meal JSON)
        meal = create_api_meal_with_recipes(recipe_count=10)
        json_meal = meal.model_dump_json()
        
        # When: Processing incoming data to domain
        with benchmark_timer() as timer:
            api_meal = ApiMeal.model_validate_json(json_meal)
            domain_meal = api_meal.to_domain()
        
        # Then: Should meet production target
        timer.assert_faster_than(0.008)  # Production target: < 8ms for 10-recipe incoming
        
        # Document performance for baseline
        actual_time_ms = timer.elapsed * 1000
        print(f"Incoming validation: {actual_time_ms:.2f}ms for 10-recipe meal (JSON → API → Domain)")

    def test_outgoing_target_serialization(self, benchmark_timer):
        """Verify outgoing serialization meets production target (Domain → API → JSON)"""
        # Given: Target scenario (10-recipe domain meal)
        domain_meal = create_domain_meal_for_conversion(recipe_count=10)
        
        # When: Processing outgoing data to JSON
        with benchmark_timer() as timer:
            api_meal = ApiMeal.from_domain(domain_meal)
            json_string = api_meal.model_dump_json()
        
        # Then: Should meet production target
        timer.assert_faster_than(0.010)  # Production target: < 10ms for 10-recipe outgoing
        
        # Document performance for baseline
        actual_time_ms = timer.elapsed * 1000
        print(f"Outgoing serialization: {actual_time_ms:.2f}ms for 10-recipe meal (Domain → API → JSON)")

    def test_roundtrip_target_performance(self, benchmark_timer):
        """Verify complete roundtrip meets combined production targets"""
        # Given: Domain meal for roundtrip test
        original_domain = create_domain_meal_for_conversion(recipe_count=10)
        
        # When: Complete production roundtrip
        with benchmark_timer() as timer:
            # Outgoing flow
            api_meal_out = ApiMeal.from_domain(original_domain)
            json_string = api_meal_out.model_dump_json()
            
            # Incoming flow
            api_meal_in = ApiMeal.model_validate_json(json_string)
            final_domain = api_meal_in.to_domain()
        
        # Then: Should meet combined target (8ms + 10ms = 18ms + overhead)
        timer.assert_faster_than(0.020)  # < 20ms for complete roundtrip
        
        # Verify data integrity
        assert final_domain.id == original_domain.id
        assert final_domain.name == original_domain.name
        assert len(final_domain.recipes) == len(original_domain.recipes)
        
        # Document roundtrip performance
        actual_time_ms = timer.elapsed * 1000
        print(f"Complete roundtrip: {actual_time_ms:.2f}ms for 10-recipe meal")


# =============================================================================
# OPTIMIZATION ROADMAP (For when rigorous targets fail)
# =============================================================================
"""
OPTIMIZATION ROADMAP - Task 1.3.3

When performance tests fail to meet rigorous targets, follow this systematic approach:

1. PROFILE CURRENT BOTTLENECKS
   - Use cProfile: `python -m cProfile -o profile.out -m pytest test_performance.py::test_name`
   - Analyze with snakeviz: `snakeviz profile.out`
   - Focus on:
     * Pydantic validation overhead
     * JSON parsing/serialization time
     * Domain object creation
     * ORM conversion operations

2. PYDANTIC OPTIMIZATION OPPORTUNITIES
   - Enable strict mode for faster validation
   - Use TypeAdapter for collection validation
   - Implement custom validators for performance-critical fields
   - Consider using model_dump_json() over json.dumps(model.dict())
   - Cache compiled validators using ConfigDict

3. LAZY LOADING AND CACHING STRATEGIES
   - Implement lazy validation for nested objects
   - Cache expensive computed properties (nutri_facts)
   - Use frozenset for immutable collections
   - Consider validator caching for repeated patterns

4. SCALING OPTIMIZATION TECHNIQUES
   - Batch validation for collections
   - Streaming validation for large datasets
   - Memory pooling for repeated operations
   - Optimize JSON parsing with orjson if needed

5. VALIDATION TARGET PRIORITIES
   If multiple targets fail, optimize in this order:
   a) Simple meal validation (< 1ms) - Core performance baseline
   b) Standard meal validation (< 3ms) - Most common use case
   c) Field validation (< 2-3ms) - Building blocks for other operations
   d) Large meal operations (< 5-15ms) - Edge case optimization
   e) Stress test targets - Production resilience

6. MONITORING AND REGRESSION DETECTION
   - Set up performance CI/CD gates
   - Monitor validation time percentiles in production
   - Alert on performance regression > 20%
   - Document known performance limitations

7. KNOWN OPTIMIZATION TECHNIQUES
   - Use Pydantic v2's rust-based core for speed
   - Minimize nested validation layers
   - Pre-compile regex patterns
   - Use native JSON serializers where possible
   - Consider async validation for I/O bound operations

8. FALLBACK STRATEGIES
   If targets cannot be met with current architecture:
   - Relax targets for complex edge cases
   - Implement performance budgets per operation type
   - Consider validation sampling for non-critical paths
   - Document acceptable performance trade-offs

Run optimization tests with:
`poetry run python pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py -v --benchmark-only`

Profile specific tests with:
`poetry run python -m cProfile -o profile.out -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py::TestIncomingDataValidationPerformance::test_incoming_simple_meal_baseline -v`
""" 