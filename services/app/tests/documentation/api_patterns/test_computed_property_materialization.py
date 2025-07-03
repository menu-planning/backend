"""
Comprehensive Computed Property Materialization Pattern Tests

This module implements Phase 1.2.2 of the API Schema Pattern Documentation project.
It validates the computed property materialization pattern, documenting how domain
@cached_property and computed properties become regular materialized fields in the API layer.

Test Coverage:
1. @cached_property nutri_facts materialization from domain to API
2. Computed properties (calorie_density, percentages) materialization
3. Cache invalidation behavior in domain vs API materialized values
4. Performance comparison: computed vs materialized access patterns
5. Composite field handling in ORM layer for materialized values
6. Edge cases: None values, empty recipes, computation failures

Pattern Being Documented:
- Domain Layer: @cached_property nutri_facts (computed on demand, cached)
- Domain Layer: Regular computed properties (always computed, no cache)
- API Layer: Regular fields with materialized values (no computation)
- ORM Layer: Composite fields storing materialized values

Design Philosophy: Validate the three-layer handling of computed properties:
Domain (computed) → API (materialized) → ORM (stored)
"""

import pytest
import time
from datetime import datetime
from typing import Any, Dict
import uuid

# Domain imports
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.enums import MeasureUnit

# API Schema imports
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts

# ORM imports
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel


class TestComputedPropertyMaterializationPattern:
    """Test suite for computed property materialization pattern documentation."""

    def test_cached_property_nutri_facts_materialization(self, sample_meal_with_nutri_facts):
        """
        Test @cached_property nutri_facts materialization from domain to API.
        
        Documents the pattern:
        - Domain: @cached_property nutri_facts (computed once, cached)
        - API: nutri_facts field (materialized value, no computation)
        - ORM: nutri_facts composite (stored materialized value)
        
        Validates:
        - Cached property computation behavior in domain
        - Materialization during from_domain() conversion
        - Materialized value preservation in API layer
        - Composite field creation for ORM persistence
        """
        domain_meal = sample_meal_with_nutri_facts
        
        # Domain Layer: Test @cached_property behavior
        # First access should trigger computation and caching
        start_time = time.perf_counter()
        first_access = domain_meal.nutri_facts
        first_access_time = time.perf_counter() - start_time
        
        # Second access should use cached value (much faster)
        start_time = time.perf_counter()
        second_access = domain_meal.nutri_facts
        second_access_time = time.perf_counter() - start_time
        
        # Validate caching behavior
        assert first_access is second_access  # Same object (cached)
        assert second_access_time < first_access_time  # Cached access faster
        
        if first_access is not None:
            assert isinstance(first_access, NutriFacts)
            assert first_access.calories.value is not None
            assert first_access.calories.value > 0
        
        # API Layer: Test materialization during conversion
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Validate materialized value matches computed value
        if domain_meal.nutri_facts is not None:
            assert api_meal.nutri_facts is not None
            assert isinstance(api_meal.nutri_facts, ApiNutriFacts)
            
            # Validate materialized values match computed values exactly
            assert api_meal.nutri_facts.calories == domain_meal.nutri_facts.calories.value
            assert api_meal.nutri_facts.protein == domain_meal.nutri_facts.protein.value
            assert api_meal.nutri_facts.carbohydrate == domain_meal.nutri_facts.carbohydrate.value
            assert api_meal.nutri_facts.total_fat == domain_meal.nutri_facts.total_fat.value
        else:
            assert api_meal.nutri_facts is None
        
        # ORM Layer: Test composite field creation
        orm_kwargs = api_meal.to_orm_kwargs()
        orm_nutri_facts = orm_kwargs["nutri_facts"]
        
        if api_meal.nutri_facts is not None:
            assert isinstance(orm_nutri_facts, NutriFactsSaModel)
            assert orm_nutri_facts.calories == domain_meal.nutri_facts.calories.value
            assert orm_nutri_facts.protein == domain_meal.nutri_facts.protein.value
        else:
            assert orm_nutri_facts is None

    def test_regular_computed_properties_materialization(self, sample_meal_with_nutri_facts):
        """
        Test regular computed properties materialization (calorie_density, percentages).
        
        Documents the pattern:
        - Domain: Regular @property methods (computed every access)
        - API: Regular fields (materialized values from domain computation)
        - ORM: Regular columns (stored materialized values)
        
        Validates:
        - Computed property behavior in domain (always computed)
        - Materialization during from_domain() conversion
        - Value accuracy across layers
        """
        domain_meal = sample_meal_with_nutri_facts
        
        # Domain Layer: Test computed properties behavior
        # These are computed on every access (no caching)
        calorie_density_1 = domain_meal.calorie_density
        calorie_density_2 = domain_meal.calorie_density
        
        carbo_percentage_1 = domain_meal.carbo_percentage
        carbo_percentage_2 = domain_meal.carbo_percentage
        
        weight_in_grams_1 = domain_meal.weight_in_grams
        weight_in_grams_2 = domain_meal.weight_in_grams
        
        # These should be equal but potentially different objects (no caching guarantee)
        assert calorie_density_1 == calorie_density_2
        assert carbo_percentage_1 == carbo_percentage_2
        assert weight_in_grams_1 == weight_in_grams_2
        
        # API Layer: Test materialization
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Validate materialized values match computed values
        assert api_meal.calorie_density == domain_meal.calorie_density
        assert api_meal.carbo_percentage == domain_meal.carbo_percentage
        assert api_meal.protein_percentage == domain_meal.protein_percentage
        assert api_meal.total_fat_percentage == domain_meal.total_fat_percentage
        assert api_meal.weight_in_grams == domain_meal.weight_in_grams
        
        # ORM Layer: Test stored values
        orm_kwargs = api_meal.to_orm_kwargs()
        
        assert orm_kwargs["calorie_density"] == domain_meal.calorie_density
        assert orm_kwargs["carbo_percentage"] == domain_meal.carbo_percentage
        assert orm_kwargs["protein_percentage"] == domain_meal.protein_percentage
        assert orm_kwargs["total_fat_percentage"] == domain_meal.total_fat_percentage
        assert orm_kwargs["weight_in_grams"] == domain_meal.weight_in_grams

    def test_computed_property_dependency_chain(self, sample_meal_with_complex_data):
        """
        Test the dependency chain: nutri_facts → macro_division → percentage properties.
        
        Documents the pattern:
        - @cached_property nutri_facts (base computation)
        - macro_division depends on nutri_facts (computed)
        - percentage properties depend on macro_division (computed)
        - All materialized as regular fields in API
        
        Validates:
        - Dependency chain integrity
        - Materialization of entire chain
        - Consistency across layers
        """
        domain_meal = sample_meal_with_complex_data
        
        # Domain Layer: Test dependency chain
        nutri_facts = domain_meal.nutri_facts
        macro_division = domain_meal.macro_division
        
        if nutri_facts is not None and macro_division is not None:
            # Validate dependency chain integrity
            carbo_pct = domain_meal.carbo_percentage
            protein_pct = domain_meal.protein_percentage
            fat_pct = domain_meal.total_fat_percentage
            
            # Percentages should sum to approximately 100%
            if all(pct is not None for pct in [carbo_pct, protein_pct, fat_pct]):
                total_percentage = carbo_pct + protein_pct + fat_pct
                assert abs(total_percentage - 100.0) < 0.01  # Allow for floating point precision
                
                # Validate individual percentages match macro_division
                assert abs(carbo_pct - macro_division.carbohydrate) < 0.01
                assert abs(protein_pct - macro_division.protein) < 0.01
                assert abs(fat_pct - macro_division.fat) < 0.01
        
        # API Layer: Test materialized dependency chain
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # All computed values should be materialized accurately
        assert api_meal.carbo_percentage == domain_meal.carbo_percentage
        assert api_meal.protein_percentage == domain_meal.protein_percentage
        assert api_meal.total_fat_percentage == domain_meal.total_fat_percentage

    def test_cache_invalidation_vs_materialization(self):
        """
        Test cache invalidation behavior in domain vs materialized values in API.
        
        Documents the pattern:
        - Domain: Cache invalidated when recipes change
        - API: Materialized values remain static (snapshot at conversion time)
        
        Validates:
        - Cache invalidation triggers recomputation in domain
        - API materialized values are immutable snapshots
        - New API conversion captures updated computed values
        """
        # Create meal with initial recipe
        meal_id = uuid.uuid4().hex
        author_id = uuid.uuid4().hex
        
        initial_recipe = _Recipe.create_recipe(
            name="Initial Recipe",
            instructions="Test cooking instructions",
            author_id=author_id,
            meal_id=meal_id,
            nutri_facts=NutriFacts(calories=200, protein=20, carbohydrate=30, total_fat=5),
            ingredients=[
                Ingredient(
                    name="Test Ingredient",
                    quantity=100,
                    unit=MeasureUnit.GRAM,
                    position=0,
                    full_text="100g Test Ingredient"
                )
            ]
        )
        
        domain_meal = Meal(
            id=meal_id,
            name="Test Meal",
            author_id=author_id,
            recipes=[initial_recipe]
        )
        
        # First API conversion - materialized values
        api_meal_1 = ApiMeal.from_domain(domain_meal)
        initial_calories_raw = api_meal_1.nutri_facts.calories if api_meal_1.nutri_facts else 0
        initial_calories = float(initial_calories_raw) if isinstance(initial_calories_raw, (int, float)) else 0.0
        
        # Add another recipe to domain meal
        additional_recipe = _Recipe.create_recipe(
            name="Additional Recipe",
            instructions="Additional cooking instructions",
            author_id=author_id,
            meal_id=meal_id,
            nutri_facts=NutriFacts(calories=150, protein=15, carbohydrate=25, total_fat=3),
            ingredients=[
                Ingredient(
                    name="Additional Ingredient",
                    quantity=100,
                    unit=MeasureUnit.GRAM,
                    position=0,
                    full_text="100g Additional Ingredient"
                )
            ]
        )
        
        # Add recipe triggers cache invalidation in domain
        domain_meal.copy_recipe(additional_recipe)
        
        # Domain: Cache should be invalidated, new computation
        updated_domain_nutri_facts = domain_meal.nutri_facts
        assert updated_domain_nutri_facts is not None
        if updated_domain_nutri_facts.calories.value is not None:
            assert updated_domain_nutri_facts.calories.value > initial_calories
        
        # API: Original materialized values remain unchanged
        assert api_meal_1.nutri_facts is not None
        original_calories_raw = api_meal_1.nutri_facts.calories
        original_calories = float(original_calories_raw) if isinstance(original_calories_raw, (int, float)) else 0.0
        assert original_calories == initial_calories
        
        # New API conversion: Captures updated computed values
        api_meal_2 = ApiMeal.from_domain(domain_meal)
        assert api_meal_2.nutri_facts is not None
        updated_calories_raw = api_meal_2.nutri_facts.calories
        
        if isinstance(updated_calories_raw, (int, float)):
            updated_calories = float(updated_calories_raw)
            assert updated_calories > initial_calories
            assert updated_calories == updated_domain_nutri_facts.calories.value

    def test_performance_computed_vs_materialized_access(self, sample_meal_with_complex_data):
        """
        Test performance characteristics: computed vs materialized access patterns.
        
        Documents the pattern:
        - Domain: First access expensive (computation), subsequent fast (cached)
        - API: All access fast (pre-materialized values)
        
        Validates:
        - Domain caching performance benefit
        - API materialized access speed
        - Performance trade-offs documented
        """
        domain_meal = sample_meal_with_complex_data
        
        # Domain: First access (computation + caching)
        start_time = time.perf_counter()
        first_nutri_facts = domain_meal.nutri_facts
        first_access_time = time.perf_counter() - start_time
        
        # Domain: Subsequent access (cached)
        start_time = time.perf_counter()
        cached_nutri_facts = domain_meal.nutri_facts
        cached_access_time = time.perf_counter() - start_time
        
        # API: Materialized conversion
        start_time = time.perf_counter()
        api_meal = ApiMeal.from_domain(domain_meal)
        materialization_time = time.perf_counter() - start_time
        
        # API: Materialized access
        start_time = time.perf_counter()
        materialized_nutri_facts = api_meal.nutri_facts
        materialized_access_time = time.perf_counter() - start_time
        
        # Performance validations
        assert cached_access_time < first_access_time  # Caching provides benefit
        assert materialized_access_time < first_access_time  # Materialized faster than computation
        
        # Content accuracy
        if first_nutri_facts is not None:
            assert first_nutri_facts is cached_nutri_facts  # Same cached object
            assert materialized_nutri_facts is not None
            
            # Handle the type variations for calories comparison
            materialized_calories = materialized_nutri_facts.calories
            if isinstance(materialized_calories, (int, float)):
                assert materialized_calories == first_nutri_facts.calories.value

    def test_edge_cases_none_values_and_empty_recipes(self):
        """
        Test edge cases: None values, empty recipes, computation failures.
        
        Documents the pattern:
        - Domain: Graceful handling of None/empty data
        - API: Proper None materialization
        - ORM: Null value storage
        
        Validates:
        - None value propagation through layers
        - Empty recipe collection handling
        - Computation failure graceful degradation
        """
        # Test with empty recipes
        empty_meal = Meal(
            id=uuid.uuid4().hex,
            name="Empty Meal",
            author_id=uuid.uuid4().hex,
            recipes=[]  # No recipes
        )
        
        # Domain: Empty recipes should return None nutri_facts
        assert empty_meal.nutri_facts is None
        assert empty_meal.calorie_density is None
        assert empty_meal.carbo_percentage is None
        assert empty_meal.weight_in_grams == 0
        
        # API: None values should be materialized as None
        api_empty_meal = ApiMeal.from_domain(empty_meal)
        assert api_empty_meal.nutri_facts is None
        assert api_empty_meal.calorie_density is None
        assert api_empty_meal.carbo_percentage is None
        assert api_empty_meal.weight_in_grams == 0
        
        # ORM: None values should be stored as None
        orm_kwargs = api_empty_meal.to_orm_kwargs()
        assert orm_kwargs["nutri_facts"] is None
        assert orm_kwargs["calorie_density"] is None
        assert orm_kwargs["carbo_percentage"] is None
        assert orm_kwargs["weight_in_grams"] == 0

    def test_composite_field_materialization_in_orm(self, sample_meal_with_nutri_facts):
        """
        Test materialized computed values storage as composite fields in ORM.
        
        Documents the pattern:
        - Domain: @cached_property nutri_facts (NutriFacts object)
        - API: nutri_facts field (ApiNutriFacts object) 
        - ORM: nutri_facts composite (NutriFactsSaModel)
        
        Validates:
        - Composite field creation from materialized values
        - Data integrity in composite structure
        - Type conversion accuracy
        """
        domain_meal = sample_meal_with_nutri_facts
        
        if domain_meal.nutri_facts is None:
            pytest.skip("Meal has no nutri_facts data for composite testing")
        
        api_meal = ApiMeal.from_domain(domain_meal)
        orm_kwargs = api_meal.to_orm_kwargs()
        
        # Validate composite field creation
        composite_nutri_facts = orm_kwargs["nutri_facts"]
        assert isinstance(composite_nutri_facts, NutriFactsSaModel)
        
        # Validate composite field data integrity
        domain_nutri_facts = domain_meal.nutri_facts
        assert composite_nutri_facts.calories == domain_nutri_facts.calories.value
        assert composite_nutri_facts.protein == domain_nutri_facts.protein.value
        assert composite_nutri_facts.carbohydrate == domain_nutri_facts.carbohydrate.value
        assert composite_nutri_facts.total_fat == domain_nutri_facts.total_fat.value
        assert composite_nutri_facts.dietary_fiber == domain_nutri_facts.dietary_fiber.value
        assert composite_nutri_facts.sugar == domain_nutri_facts.sugar.value
        assert composite_nutri_facts.sodium == domain_nutri_facts.sodium.value
        assert composite_nutri_facts.saturated_fat == domain_nutri_facts.saturated_fat.value

    def test_materialization_accuracy_with_complex_computations(self, sample_meal_with_complex_data):
        """
        Test materialization accuracy for complex computed properties.
        
        Documents the pattern:
        - Domain: Complex computations with multiple dependencies
        - API: All complex computations materialized as simple fields
        - ORM: Complex results stored as simple values
        
        Validates:
        - Complex computation accuracy
        - Materialization preserves precision
        - No computational drift across layers
        """
        domain_meal = sample_meal_with_complex_data
        
        if domain_meal.nutri_facts is None:
            pytest.skip("Meal has no nutri_facts for complex computation testing")
        
        # Domain: Get all computed values
        domain_values = {
            'nutri_facts_calories': domain_meal.nutri_facts.calories.value,
            'calorie_density': domain_meal.calorie_density,
            'carbo_percentage': domain_meal.carbo_percentage,
            'protein_percentage': domain_meal.protein_percentage,
            'total_fat_percentage': domain_meal.total_fat_percentage,
            'weight_in_grams': domain_meal.weight_in_grams
        }
        
        # API: Materialized values
        api_meal = ApiMeal.from_domain(domain_meal)
        api_values = {
            'nutri_facts_calories': api_meal.nutri_facts.calories if api_meal.nutri_facts else None,
            'calorie_density': api_meal.calorie_density,
            'carbo_percentage': api_meal.carbo_percentage,
            'protein_percentage': api_meal.protein_percentage,
            'total_fat_percentage': api_meal.total_fat_percentage,
            'weight_in_grams': api_meal.weight_in_grams
        }
        
        # ORM: Stored values
        orm_kwargs = api_meal.to_orm_kwargs()
        orm_values = {
            'nutri_facts_calories': orm_kwargs["nutri_facts"].calories if orm_kwargs["nutri_facts"] else None,
            'calorie_density': orm_kwargs["calorie_density"],
            'carbo_percentage': orm_kwargs["carbo_percentage"],
            'protein_percentage': orm_kwargs["protein_percentage"],
            'total_fat_percentage': orm_kwargs["total_fat_percentage"],
            'weight_in_grams': orm_kwargs["weight_in_grams"]
        }
        
        # Validate exact precision preservation across all layers
        for key in domain_values:
            domain_val = domain_values[key]
            api_val = api_values[key]
            orm_val = orm_values[key]
            
            if domain_val is None:
                assert api_val is None
                assert orm_val is None
            else:
                # For floating point values, allow minimal precision difference
                if isinstance(domain_val, float):
                    assert abs(api_val - domain_val) < 1e-10
                    assert abs(orm_val - domain_val) < 1e-10
                else:
                    assert api_val == domain_val
                    assert orm_val == domain_val 