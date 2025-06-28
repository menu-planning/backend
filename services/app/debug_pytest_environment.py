#!/usr/bin/env python3
"""
Debug script to investigate why macro_division fails in pytest environment but works in isolation.
"""

import sys
import pytest
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_domain_factories import create_meal, reset_meal_domain_counters
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.recipe.recipe_domain_factories import create_recipe_kwargs, reset_recipe_domain_counters
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.shared_domain_factories import reset_tag_domain_counters

def create_recipe_for_meal(meal_id: str, author_id: str, **recipe_kwargs):
    """Helper to create recipe with correct meal_id and author_id."""
    kwargs = create_recipe_kwargs(
        meal_id=meal_id,
        author_id=author_id,
        **recipe_kwargs
    )
    from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
    return _Recipe(**kwargs)

def setup_method_simulation():
    """Simulate the setup_method from the test class."""
    reset_meal_domain_counters()
    reset_recipe_domain_counters()
    reset_tag_domain_counters()

def deep_debug_macro_division_failure(calories, carbs, protein, fat, test_name):
    """Deep investigation of why macro_division returns None in pytest environment."""
    print(f"\n🔬 DEEP DEBUG: {test_name}")
    print(f"Input: calories={calories}, carbs={carbs}, protein={protein}, fat={fat}")
    
    # Step 1: Create meal (like in test)
    meal = create_meal(name="Debug Meal")
    print(f"✅ Created meal: {meal.id}")
    
    # Step 2: Create recipe (like in test)
    recipe = create_recipe_for_meal(
        meal_id=meal.id,
        author_id=meal.author_id,
        name="Debug Recipe",
        nutri_facts=NutriFacts(
            calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM)
        )
    )
    print(f"✅ Created recipe: {recipe.id}")
    
    # Step 3: Update meal with recipe (like in test)
    meal.update_properties(recipes=[recipe])
    print(f"✅ Updated meal with recipe")
    
    # Step 4: Check nutri_facts step by step
    print(f"\n🧪 Testing nutri_facts...")
    nutri_facts = meal.nutri_facts
    print(f"   nutri_facts: {nutri_facts is not None}")
    if nutri_facts:
        print(f"   carb value: {nutri_facts.carbohydrate.value}")
        print(f"   protein value: {nutri_facts.protein.value}")
        print(f"   fat value: {nutri_facts.total_fat.value}")
    else:
        print(f"   ❌ nutri_facts is None!")
        return None
    
    # Step 5: Check macro_division logic step by step
    print(f"\n🧪 Testing macro_division logic...")
    
    # Check step by step what macro_division does
    print(f"   1. Checking meal.nutri_facts exists...")
    if not meal.nutri_facts:
        print(f"      ❌ meal.nutri_facts is None - returning None")
        return None
    print(f"      ✅ meal.nutri_facts exists")
    
    print(f"   2. Extracting macro values...")
    carb_val = meal.nutri_facts.carbohydrate.value
    protein_val = meal.nutri_facts.protein.value 
    fat_val = meal.nutri_facts.total_fat.value
    print(f"      carb: {carb_val}, protein: {protein_val}, fat: {fat_val}")
    
    print(f"   3. Checking for None values...")
    if carb_val is None or protein_val is None or fat_val is None:
        print(f"      ❌ One or more values is None - returning None")
        return None
    print(f"      ✅ All values are not None")
    
    print(f"   4. Calculating denominator...")
    denominator = carb_val + protein_val + fat_val
    print(f"      denominator: {denominator}")
    
    print(f"   5. Checking denominator for zero...")
    if denominator == 0:
        print(f"      ❌ Denominator is zero - returning None")
        return None
    print(f"      ✅ Denominator is not zero")
    
    # Step 6: Check actual macro_division call
    print(f"\n🎯 Calling actual macro_division property...")
    macro_div = meal.macro_division
    print(f"   Result: {macro_div}")
    
    if macro_div is None:
        print(f"   ❌ FAILURE: macro_division returned None despite valid inputs!")
        
        # Additional debugging - check cache state
        cache_info = meal.get_cache_info()
        print(f"   Cache info: {cache_info}")
        
        # Check if macro_division was computed
        computed_caches = meal._computed_caches
        print(f"   Computed caches: {computed_caches}")
        
        # Try accessing nutri_facts again
        print(f"\n🔍 Re-checking nutri_facts after macro_division call...")
        nutri_facts_2 = meal.nutri_facts
        print(f"   nutri_facts (2nd call): {nutri_facts_2 is not None}")
        
        return None
    else:
        print(f"   ✅ SUCCESS: macro_division returned valid result")
        print(f"      carb %: {macro_div.carbohydrate:.2f}")
        print(f"      protein %: {macro_div.protein:.2f}")
        print(f"      fat %: {macro_div.fat:.2f}")
        return macro_div

def test_single_case_in_pytest_style():
    """Test a single case using pytest-style setup."""
    print("\n" + "="*80)
    print("TESTING SINGLE CASE IN PYTEST STYLE")
    print("="*80)
    
    # Simulate setup_method
    setup_method_simulation()
    
    # Test the failing case: (10000.0, 1000.0, 1000.0, 1000.0)
    result = deep_debug_macro_division_failure(10000.0, 1000.0, 1000.0, 1000.0, "High Nutrition")
    return result is not None

def test_multiple_cases_in_sequence():
    """Test multiple cases in sequence like pytest does."""
    print("\n" + "="*80)
    print("TESTING MULTIPLE CASES IN SEQUENCE (LIKE PYTEST)")
    print("="*80)
    
    test_cases = [
        (0.0, 0.0, 0.0, 0.0),  # Should pass
        (10000.0, 1000.0, 1000.0, 1000.0),  # Should fail in pytest
        (0.001, 0.001, 0.001, 0.001),  # Should fail in pytest
    ]
    
    results = []
    for i, (calories, carbs, protein, fat) in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"TEST CASE {i}: ({calories}, {carbs}, {protein}, {fat})")
        print(f"{'='*50}")
        
        # Setup for each test (like pytest does)
        setup_method_simulation()
        
        result = deep_debug_macro_division_failure(calories, carbs, protein, fat, f"Case {i}")
        results.append(result is not None)
        
        # Small delay to see if timing matters
        import time
        time.sleep(0.01)
    
    print(f"\n📊 SUMMARY:")
    for i, (case, result) in enumerate(zip(test_cases, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   Case {i} {case}: {status}")
    
    return results

def main():
    """Run comprehensive investigation."""
    print("🔬 INVESTIGATING PYTEST ENVIRONMENT FLAKY BEHAVIOR")
    print("=" * 80)
    
    # Test 1: Single case
    single_result = test_single_case_in_pytest_style()
    
    # Test 2: Multiple cases in sequence  
    sequence_results = test_multiple_cases_in_sequence()
    
    print(f"\n🏁 FINAL RESULTS:")
    print(f"   Single case test: {'✅ PASS' if single_result else '❌ FAIL'}")
    print(f"   Sequence test results: {sequence_results}")
    
    if not single_result or not all(sequence_results[1:]):  # Skip first (zero case)
        print(f"\n💡 CONCLUSION: Successfully reproduced pytest environment issue!")
    else:
        print(f"\n🤔 CONCLUSION: Could not reproduce issue in this simulation.")

if __name__ == "__main__":
    main() 