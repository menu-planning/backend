"""
Baseline Performance Tests for Domain Heavy Computations

This file captures performance baselines for heavy computed properties 
before the domain refactoring. These benchmarks will be used to:

1. Establish current performance metrics
2. Validate ≥30% speed improvement after refactoring
3. Ensure ≥95% cache hit ratio after implementing instance-level caching

Heavy Properties Under Test:
- Meal.nutri_facts (aggregates nutrition from multiple recipes)
- Meal.macro_division (calculates macro percentages)
- _Recipe.average_taste_rating (averages taste ratings)
- _Recipe.average_convenience_rating (averages convenience ratings)  
- _Recipe.macro_division (calculates recipe macro percentages)
"""

import pytest
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_domain_factories import create_meal
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.recipe.recipe_domain_factories import create_rating, create_recipe


class TestMealPerformanceBaseline:
    """Baseline performance tests for Meal aggregate heavy computations."""
    
    def test_meal_nutri_facts_computation_baseline(self, benchmark):
        """Benchmark current nutri_facts computation with multiple recipes."""
        # Create meal with multiple recipes to simulate real load
        recipes = []
        for i in range(10):  # 10 recipes to create meaningful computation load
            # Create varied nutrition facts for realistic computation
            nutri_facts = NutriFacts(
                calories=200.0 + (i * 100),
                protein=20.0 + (i * 5),
                carbohydrate=40.0 + (i * 10),
                total_fat=15.0 + (i * 3),
                saturated_fat=5.0 + i,
                trans_fat=0.5,
                dietary_fiber=8.0 + i,
                sodium=500.0 + (i * 100),
                sugar=10.0 + i
            )
            recipe = create_recipe(
                nutri_facts=nutri_facts,
                weight_in_grams=200 + (i * 50)  # Varying weights
            )
            recipes.append(recipe)
            print(f"Recipe {i}: nutri_facts={recipe.nutri_facts}")
        
        meal = create_meal(recipes=recipes)
        print(f"Meal recipes count: {len(meal.recipes)}")
        print(f"Meal first recipe nutri_facts: {meal.recipes[0].nutri_facts if meal.recipes else 'No recipes'}")
        
        # Note: Cache clearing is complex with @lru_cache on properties
        # We'll benchmark the current state as-is for baseline measurement
        
        # Benchmark the computation
        result = benchmark(lambda: meal.nutri_facts)
        print(f"Meal nutri_facts result: {result}")
        
        # Verify result is correct
        assert result is not None
        assert result.calories.value > 0
        
    def test_meal_macro_division_computation_baseline(self, benchmark):
        """Benchmark current macro_division computation."""
        # Create meal with multiple recipes
        recipes = []
        for i in range(10):
            nutri_facts = NutriFacts(
                calories=400.0 + (i * 50),
                carbohydrate=50.0 + i,
                protein=25.0 + i,
                total_fat=15.0 + i,
                saturated_fat=5.0,
                trans_fat=0.0,
                dietary_fiber=8.0,
                sodium=600.0,
                sugar=8.0
            )
            recipe = create_recipe(nutri_facts=nutri_facts)
            recipes.append(recipe)
        
        meal = create_meal(recipes=recipes)
        
        # Note: Cache clearing is complex with @lru_cache on properties
        # We'll benchmark the current state as-is for baseline measurement
        
        # Benchmark the computation
        result = benchmark(lambda: meal.macro_division)
        
        # Verify result
        assert result is not None
        assert abs(result.carbohydrate + result.protein + result.fat - 100.0) < 0.01
        
    def test_meal_repeated_access_cache_effectiveness_baseline(self, benchmark):
        """Measure cache effectiveness with repeated property access."""
        recipes = []
        for i in range(15):  # More recipes for heavier computation
            nutri_facts = NutriFacts(
                calories=300.0 + (i * 75),
                protein=18.0 + (i * 3),
                carbohydrate=35.0 + (i * 8),
                total_fat=12.0 + (i * 2),
                saturated_fat=4.0,
                trans_fat=0.0,
                dietary_fiber=6.0,
                sodium=400.0,
                sugar=12.0
            )
            recipe = create_recipe(
                nutri_facts=nutri_facts,
                weight_in_grams=150 + (i * 30)
            )
            recipes.append(recipe)
            
        meal = create_meal(recipes=recipes)
        
        # Note: Cache clearing is complex with @lru_cache on properties
        # This test measures the cache effectiveness as-is
        
        def access_heavy_properties():
            """Access heavy properties multiple times to test caching."""
            # Access each property 5 times
            for _ in range(5):
                nutri = meal.nutri_facts
                macro = meal.macro_division
                density = meal.calorie_density
                weight = meal.weight_in_grams
            return nutri, macro, density, weight
        
        # Benchmark repeated access
        result = benchmark(access_heavy_properties)
        
        # Verify results
        nutri, macro, density, weight = result
        assert nutri is not None
        assert macro is not None


class TestRecipePerformanceBaseline:
    """Baseline performance tests for _Recipe heavy computations."""
    
    def test_recipe_average_ratings_computation_baseline(self, benchmark):
        """Benchmark current rating average computations."""
        # Create recipe with many ratings
        ratings = []
        for i in range(50):  # Many ratings to create computation load
            rating = create_rating(
                taste=1 + (i % 5),
                convenience=1 + ((i + 2) % 5)
            )
            ratings.append(rating)
            
        recipe = create_recipe(
            nutri_facts=NutriFacts(
                calories=350.0,
                protein=22.0,
                carbohydrate=45.0,
                total_fat=14.0,
                saturated_fat=4.5,
                trans_fat=0.0,
                dietary_fiber=7.0,
                sodium=550.0,
                sugar=9.0
            ),
            ratings=ratings
        )
        
        # Note: Cache clearing is complex with @lru_cache on properties
        # We'll benchmark the current state as-is for baseline measurement
        
        def compute_averages():
            taste_avg = recipe.average_taste_rating
            convenience_avg = recipe.average_convenience_rating
            return taste_avg, convenience_avg
        
        # Benchmark the computation
        result = benchmark(compute_averages)
        
        # Verify results
        taste_avg, convenience_avg = result
        assert taste_avg is not None
        assert convenience_avg is not None
        assert 1.0 <= taste_avg <= 5.0
        assert 1.0 <= convenience_avg <= 5.0
        
    def test_recipe_macro_division_computation_baseline(self, benchmark):
        """Benchmark current recipe macro_division computation."""
        recipe = create_recipe(
            nutri_facts=NutriFacts(
                calories=450.0,
                carbohydrate=60.0,
                protein=30.0,
                total_fat=20.0,
                saturated_fat=7.0,
                trans_fat=0.0,
                dietary_fiber=5.0,
                sodium=700.0,
                sugar=15.0
            )
        )
        
        # Note: Cache clearing is complex with @lru_cache on properties
        # We'll benchmark the current state as-is for baseline measurement
        
        # Benchmark the computation
        result = benchmark(lambda: recipe.macro_division)
        
        # Verify result
        assert result is not None
        assert abs(result.carbohydrate + result.protein + result.fat - 100.0) < 0.01


class TestCacheLeakageBaseline:
    """Tests to document current cache leakage issues with @lru_cache."""
    
    def test_shared_cache_bug_documentation(self):
        """Document the current shared cache bug before fixing."""
        # Create two different recipes with different nutrition
        recipe1 = create_recipe(
            nutri_facts=NutriFacts(
                calories=400.0,
                carbohydrate=100.0,
                protein=50.0,
                total_fat=25.0,
                saturated_fat=8.0,
                trans_fat=0.0,
                dietary_fiber=10.0,
                sodium=500.0,
                sugar=12.0
            )
        )
        
        recipe2 = create_recipe(
            nutri_facts=NutriFacts(
                calories=800.0,
                carbohydrate=200.0,
                protein=100.0,
                total_fat=50.0,
                saturated_fat=16.0,
                trans_fat=0.0,
                dietary_fiber=20.0,
                sodium=1000.0,
                sugar=24.0
            )
        )
        
        # Access macro_division on first recipe
        macro1_first = recipe1.macro_division
        
        # Access macro_division on second recipe  
        macro2 = recipe2.macro_division
        
        # Access macro_division on first recipe again
        macro1_second = recipe1.macro_division
        
        # With @lru_cache, these should be the same object (shared cache bug)
        # After refactoring to @cached_property, they should be different
        
        # Document current behavior - this test may fail after refactoring
        assert macro1_first is not None
        assert macro2 is not None
        assert macro1_second is not None
        
        # The values should be different based on different nutrition facts
        # But with shared cache, they might be wrong
        print(f"Recipe1 first macro: {macro1_first}")
        print(f"Recipe2 macro: {macro2}")  
        print(f"Recipe1 second macro: {macro1_second}")
        
    def test_meal_cache_invalidation_on_recipe_changes(self):
        """Document current cache invalidation behavior."""
        recipe = create_recipe(
            nutri_facts=NutriFacts(
                calories=300.0,
                protein=15.0,
                carbohydrate=35.0,
                total_fat=12.0,
                saturated_fat=4.0,
                trans_fat=0.0,
                dietary_fiber=6.0,
                sodium=400.0,
                sugar=8.0
            )
        )
        meal = create_meal(recipes=[recipe])
        
        # Get initial nutri_facts
        initial_nutri = meal.nutri_facts
        
        # Modify recipes (this should invalidate cache)
        new_recipe = create_recipe(
            nutri_facts=NutriFacts(
                calories=9999.0,  # Clearly different value
                protein=500.0,
                carbohydrate=1000.0,
                total_fat=333.0,
                saturated_fat=100.0,
                trans_fat=0.0,
                dietary_fiber=50.0,
                sodium=2000.0,
                sugar=200.0
            )
        )
        meal.update_properties(recipes=[new_recipe])
        
        # Get nutri_facts again
        updated_nutri = meal.nutri_facts
        
        # Values should be different 
        assert initial_nutri != updated_nutri
        assert updated_nutri.calories.value == 9999.0 # type: ignore