#!/usr/bin/env python3
"""
Debug script to reproduce and analyze the flaky test behavior.
"""

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_domain_factories import create_meal, reset_meal_domain_counters
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.recipe.recipe_domain_factories import create_recipe_kwargs, reset_recipe_domain_counters
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.shared_domain_factories import reset_tag_domain_counters

def reset_all_counters():
    """Reset all domain factory counters for clean state."""
    reset_meal_domain_counters()
    reset_recipe_domain_counters()
    reset_tag_domain_counters()

def create_recipe_for_meal(meal_id: str, author_id: str, **recipe_kwargs):
    """Helper to create recipe with correct meal_id and author_id."""
    kwargs = create_recipe_kwargs(
        meal_id=meal_id,
        author_id=author_id,
        **recipe_kwargs
    )
    from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
    return _Recipe(**kwargs)

def debug_extreme_nutrition_case(calories, carbs, protein, fat, run_number):
    """Debug a specific extreme nutrition test case."""
    print(f"\n=== Run {run_number}: Testing case ({calories}, {carbs}, {protein}, {fat}) ===")
    
    # Reset state
    reset_all_counters()
    
    # Create meal
    meal = create_meal(name="Extreme Nutrition Meal")
    print(f"Created meal: {meal.id}")
    
    # Create recipe with extreme nutrition
    recipe = create_recipe_for_meal(
        meal_id=meal.id,
        author_id=meal.author_id,
        name="Extreme Nutrition Recipe",
        nutri_facts=NutriFacts(
            calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM)
        )
    )
    
    print(f"Created recipe with nutrition:")
    print(f"  calories: {recipe.nutri_facts.calories.value if recipe.nutri_facts else 'None'}")
    print(f"  carbs: {recipe.nutri_facts.carbohydrate.value if recipe.nutri_facts else 'None'}")
    print(f"  protein: {recipe.nutri_facts.protein.value if recipe.nutri_facts else 'None'}")
    print(f"  fat: {recipe.nutri_facts.total_fat.value if recipe.nutri_facts else 'None'}")
    
    # Update meal with recipe
    meal.update_properties(recipes=[recipe])
    print(f"Updated meal with recipe")
    
    # Check meal nutrition
    meal_nutrition = meal.nutri_facts
    print(f"Meal nutrition: {meal_nutrition}")
    if meal_nutrition:
        print(f"  calories: {meal_nutrition.calories.value}")
        print(f"  carbs: {meal_nutrition.carbohydrate.value}")
        print(f"  protein: {meal_nutrition.protein.value}")
        print(f"  fat: {meal_nutrition.total_fat.value}")
    
    # Check macro division
    macro_div = meal.macro_division
    print(f"Macro division: {macro_div}")
    
    total_macros = carbs + protein + fat
    print(f"Expected total_macros: {total_macros}")
    
    if total_macros > 0:
        expected_result = "NOT None"
        actual_result = "None" if macro_div is None else "NOT None"
        status = "✅ PASS" if macro_div is not None else "❌ FAIL"
        print(f"Test result: {status} (expected: {expected_result}, actual: {actual_result})")
        
        if macro_div is not None:
            print(f"  carb %: {macro_div.carbohydrate:.2f}")
            print(f"  protein %: {macro_div.protein:.2f}")
            print(f"  fat %: {macro_div.fat:.2f}")
    else:
        expected_result = "None"
        actual_result = "None" if macro_div is None else "NOT None"
        status = "✅ PASS" if macro_div is None else "❌ FAIL"
        print(f"Test result: {status} (expected: {expected_result}, actual: {actual_result})")
    
    # Check cache info
    cache_info = meal.get_cache_info()
    print(f"Cache info: {cache_info}")
    
    return macro_div is not None if total_macros > 0 else macro_div is None

def main():
    """Run debug scenarios to understand the flaky behavior."""
    print("🐛 Debugging Flaky Test: test_meal_with_extreme_nutrition_values")
    
    # Test cases from the parametrized test
    test_cases = [
        (0.0, 0.0, 0.0, 0.0),  # All zero nutrition - should always pass
        (10000.0, 1000.0, 1000.0, 1000.0),  # Extremely high nutrition - flaky
        (0.001, 0.001, 0.001, 0.001),  # Minimal nutrition - flaky
        (5000.0, 0.0, 500.0, 0.0),  # Only protein - flaky
        (3000.0, 500.0, 0.0, 0.0),  # Only carbs - flaky
        (2000.0, 0.0, 0.0, 200.0),  # Only fat - flaky
    ]
    
    # Run each test case multiple times to see flaky behavior
    for case_idx, test_case in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"TEST CASE {case_idx}: {test_case}")
        print(f"{'='*60}")
        
        results = []
        for run in range(5):
            try:
                result = debug_extreme_nutrition_case(*test_case, run + 1)
                results.append(result)
            except Exception as e:
                print(f"❌ ERROR in run {run + 1}: {e}")
                results.append(False)
        
        # Analyze results
        passed = sum(results)
        total = len(results)
        consistency = "CONSISTENT" if passed == 0 or passed == total else "FLAKY"
        
        print(f"\nSUMMARY for case {test_case}:")
        print(f"  Passed: {passed}/{total}")
        print(f"  Status: {consistency}")
        
        if consistency == "FLAKY":
            print(f"  🔥 FLAKY BEHAVIOR DETECTED!")

if __name__ == "__main__":
    main() 