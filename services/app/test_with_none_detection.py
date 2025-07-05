#!/usr/bin/env python3
"""
Simple pytest-style test with None detection.
"""

import pytest
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from tests.contexts.recipes_catalog.data_factories.meal.meal_domain_factories import create_meal, reset_meal_domain_counters
from tests.contexts.recipes_catalog.data_factories.recipe.recipe_domain_factories import create_recipe_kwargs, reset_recipe_domain_counters
from tests.contexts.recipes_catalog.data_factories.shared_domain_factories import reset_tag_domain_counters

def create_recipe_for_meal(meal_id: str, author_id: str, **recipe_kwargs):
    """Helper to create recipe with correct meal_id and author_id."""
    kwargs = create_recipe_kwargs(
        meal_id=meal_id,
        author_id=author_id,
        **recipe_kwargs
    )
    from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
    return _Recipe(**kwargs)

def setup_method():
    """Setup like the real test."""
    reset_meal_domain_counters()
    reset_recipe_domain_counters()
    reset_tag_domain_counters()

def debug_single_case(calories, carbs, protein, fat, case_name):
    """Debug a single test case with detailed None detection."""
    print(f"\n🔍 DEBUGGING CASE: {case_name}")
    print(f"   Input: ({calories}, {carbs}, {protein}, {fat})")
    
    # Setup (like real test)
    setup_method()
    
    # Create meal
    meal = create_meal(name="Test Meal")
    print(f"   ✅ Created meal: {meal.id}")
    
    # Create recipe with NutriFacts
    print(f"   🧪 Creating NutriFacts...")
    try:
        nutri_facts = NutriFacts(
            calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM)
        )
        print(f"   ✅ NutriFacts created successfully")
        
        # Check the values in NutriFacts
        print(f"   📊 NutriFacts values after creation:")
        print(f"      carb: {nutri_facts.carbohydrate.value} (None? {nutri_facts.carbohydrate.value is None})")
        print(f"      protein: {nutri_facts.protein.value} (None? {nutri_facts.protein.value is None})")
        print(f"      fat: {nutri_facts.total_fat.value} (None? {nutri_facts.total_fat.value is None})")
        
    except Exception as e:
        print(f"   ❌ Error creating NutriFacts: {e}")
        return False
    
    # Create recipe
    recipe = create_recipe_for_meal(
        meal_id=meal.id,
        author_id=meal.author_id,
        name="Test Recipe",
        nutri_facts=nutri_facts
    )
    print(f"   ✅ Created recipe: {recipe.id}")
    
    # Update meal
    meal.update_properties(recipes=[recipe])
    print(f"   ✅ Updated meal with recipe")
    
    # Check nutri_facts on meal
    print(f"   🧪 Checking meal.nutri_facts...")
    meal_nutri_facts = meal.nutri_facts
    if meal_nutri_facts:
        print(f"   📊 Meal nutri_facts values:")
        print(f"      carb: {meal_nutri_facts.carbohydrate.value} (None? {meal_nutri_facts.carbohydrate.value is None})")
        print(f"      protein: {meal_nutri_facts.protein.value} (None? {meal_nutri_facts.protein.value is None})")
        print(f"      fat: {meal_nutri_facts.total_fat.value} (None? {meal_nutri_facts.total_fat.value is None})")
    else:
        print(f"   ❌ meal.nutri_facts is None!")
        return False
    
    # Test macro_division  
    print(f"   🎯 Calling macro_division...")
    macro_div = meal.macro_division
    print(f"   📊 Result: {macro_div}")
    
    if macro_div is None:
        print(f"   ❌ MACRO_DIVISION RETURNED NONE!")
        
        # Additional debugging
        print(f"   🔍 Additional debugging:")
        
        # Try calling macro_division again
        print(f"      Calling macro_division again...")
        macro_div2 = meal.macro_division
        print(f"      Second result: {macro_div2}")
        
        # Check cache state
        cache_info = meal.get_cache_info()
        print(f"      Cache info: {cache_info}")
        
        return False
    else:
        print(f"   ✅ SUCCESS: {macro_div}")
        return True

def test_meal_with_extreme_nutrition_values():
    """Replicate the exact failing test with None detection."""
    print("🧪 REPLICATING EXACT FAILING TEST WITH NONE DETECTION")
    print("=" * 80)
    
    test_cases = [
        (0.0, 0.0, 0.0, 0.0),  # Zero case (usually passes)
        (10000.0, 1000.0, 1000.0, 1000.0),  # High nutrition (usually fails)
        (0.001, 0.001, 0.001, 0.001),  # Minimal nutrition (usually fails)
        (5000.0, 0.0, 500.0, 0.0),  # Only protein (usually fails)
        (3000.0, 500.0, 0.0, 0.0),  # Only carbs (usually fails)
        (2000.0, 0.0, 0.0, 200.0),  # Only fat (usually fails)
    ]
    
    results = []
    for i, (calories, carbs, protein, fat) in enumerate(test_cases):
        case_name = f"Case {i}: ({calories}, {carbs}, {protein}, {fat})"
        result = debug_single_case(calories, carbs, protein, fat, case_name)
        results.append(result)
        
        print(f"\n   📊 Case {i} result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print(f"\n🏁 FINAL SUMMARY:")
    for i, (case, result) in enumerate(zip(test_cases, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   Case {i} {case}: {status}")
    
    # Count failures
    failures = sum(1 for r in results if not r)
    print(f"\n📈 FAILURE RATE: {failures}/{len(test_cases)} = {failures/len(test_cases)*100:.1f}%")
    
    if failures > 0:
        print(f"🔥 FLAKY BEHAVIOR REPRODUCED!")
    else:
        print(f"🤔 No failures detected in this run.")

if __name__ == "__main__":
    test_meal_with_extreme_nutrition_values() 