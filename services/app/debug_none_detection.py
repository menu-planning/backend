#!/usr/bin/env python3
"""
Debug script to detect None values in macro nutrients and test permissive logic.
"""

import functools
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.recipes_catalog.core.domain.meal.value_objects.macro_division import MacroDivision
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

def permissive_macro_division_logic(nutri_facts):
    """Alternative macro_division logic that treats None as 0."""
    print(f"\n🔄 PERMISSIVE MACRO_DIVISION LOGIC:")
    
    if not nutri_facts:
        print(f"   ❌ No nutri_facts")
        return None
        
    # Get values, treating None as 0.0
    carb = nutri_facts.carbohydrate.value
    protein = nutri_facts.protein.value
    fat = nutri_facts.total_fat.value
    
    print(f"   Raw values: carb={carb}, protein={protein}, fat={fat}")
    
    # Convert None to 0.0 (permissive approach)
    carb = carb if carb is not None else 0.0
    protein = protein if protein is not None else 0.0
    fat = fat if fat is not None else 0.0
    
    print(f"   Converted values: carb={carb}, protein={protein}, fat={fat}")
    
    denominator = carb + protein + fat
    print(f"   Denominator: {denominator}")
    
    if denominator == 0:
        print(f"   ❌ All macros are zero")
        return None
        
    result = MacroDivision(
        carbohydrate=(carb / denominator) * 100,
        protein=(protein / denominator) * 100,
        fat=(fat / denominator) * 100,
    )
    print(f"   ✅ Created: {result}")
    return result

def strict_macro_division_logic(nutri_facts):
    """Current strict macro_division logic that requires all non-None."""
    print(f"\n🔒 STRICT MACRO_DIVISION LOGIC:")
    
    if not nutri_facts:
        print(f"   ❌ No nutri_facts")
        return None
        
    carb = nutri_facts.carbohydrate.value
    protein = nutri_facts.protein.value
    fat = nutri_facts.total_fat.value
    
    print(f"   Values: carb={carb}, protein={protein}, fat={fat}")
    
    # Current strict logic - ANY None causes failure
    if carb is None or protein is None or fat is None:
        print(f"   ❌ One or more values is None")
        return None
        
    denominator = carb + protein + fat
    print(f"   Denominator: {denominator}")
    
    if denominator == 0:
        print(f"   ❌ Denominator is zero")
        return None
        
    result = MacroDivision(
        carbohydrate=(carb / denominator) * 100,
        protein=(protein / denominator) * 100,
        fat=(fat / denominator) * 100,
    )
    print(f"   ✅ Created: {result}")
    return result

def debug_macro_division_with_detection(self):
    """Patched macro_division that detects and reports None values."""
    print(f"\n🕵️ NONE-DETECTION MACRO_DIVISION:")
    
    self._check_not_discarded()
    
    if not self.nutri_facts:
        print(f"   ❌ nutri_facts is falsy")
        return None
        
    carb = self.nutri_facts.carbohydrate.value
    protein = self.nutri_facts.protein.value
    fat = self.nutri_facts.total_fat.value
    
    print(f"   🔍 DETECTED VALUES:")
    print(f"     carb: {carb} (is None: {carb is None})")
    print(f"     protein: {protein} (is None: {protein is None})")
    print(f"     fat: {fat} (is None: {fat is None})")
    
    # Check for None values
    none_values = []
    if carb is None:
        none_values.append("carb")
    if protein is None:
        none_values.append("protein") 
    if fat is None:
        none_values.append("fat")
        
    if none_values:
        print(f"   🔥 NONE VALUES DETECTED: {none_values}")
        print(f"   ❌ Returning None due to strict logic")
        return None
    else:
        print(f"   ✅ No None values detected")
        
    denominator = carb + protein + fat
    if denominator == 0:
        print(f"   ❌ Denominator is zero")
        return None
        
    result = MacroDivision(
        carbohydrate=(carb / denominator) * 100,
        protein=(protein / denominator) * 100,
        fat=(fat / denominator) * 100,
    )
    print(f"   ✅ Returning: {result}")
    return result

def test_business_logic_approaches():
    """Test both strict and permissive approaches with test cases."""
    print(f"\n📊 TESTING BUSINESS LOGIC APPROACHES")
    print(f"=" * 60)
    
    # Test cases that might have None values
    test_cases = [
        {"name": "All valid", "carb": 1000.0, "protein": 1000.0, "fat": 1000.0},
        {"name": "Carb None", "carb": None, "protein": 1000.0, "fat": 1000.0},
        {"name": "Protein None", "carb": 1000.0, "protein": None, "fat": 1000.0},
        {"name": "Fat None", "carb": 1000.0, "protein": 1000.0, "fat": None},
        {"name": "All None", "carb": None, "protein": None, "fat": None},
        {"name": "Mixed", "carb": 500.0, "protein": None, "fat": 300.0},
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        
        # Create mock nutri_facts
        try:
            nutri_facts = NutriFacts(
                calories=NutriValue(value=2000.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=case['carb'], unit=MeasureUnit.GRAM),
                protein=NutriValue(value=case['protein'], unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=case['fat'], unit=MeasureUnit.GRAM)
            )
            
            strict_result = strict_macro_division_logic(nutri_facts)
            permissive_result = permissive_macro_division_logic(nutri_facts)
            
            print(f"   Strict result: {'✅ SUCCESS' if strict_result else '❌ NONE'}")
            print(f"   Permissive result: {'✅ SUCCESS' if permissive_result else '❌ NONE'}")
            
        except Exception as e:
            print(f"   ❌ Error creating nutri_facts: {e}")

def test_with_none_detection():
    """Test with None detection patch."""
    print(f"\n🧪 TESTING WITH NONE DETECTION PATCH")
    print(f"=" * 60)
    
    # Reset state
    reset_meal_domain_counters()
    reset_recipe_domain_counters()
    reset_tag_domain_counters()
    
    # Create meal and recipe
    meal = create_meal(name="Debug Meal")
    recipe = create_recipe_for_meal(
        meal_id=meal.id,
        author_id=meal.author_id,
        name="Debug Recipe",
        nutri_facts=NutriFacts(
            calories=NutriValue(value=10000.0, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=1000.0, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=1000.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=1000.0, unit=MeasureUnit.GRAM)
        )
    )
    
    meal.update_properties(recipes=[recipe])
    
    # Patch the property temporarily
    original_property = Meal.macro_division
    patched_property = functools.cached_property(debug_macro_division_with_detection)
    setattr(Meal, 'macro_division', patched_property)
    
    try:
        # Clear cache to force recalculation with proper handling
        if hasattr(meal, '_computed_caches'):
            # Check if it's a mutable collection first
            computed_caches = getattr(meal, '_computed_caches')
            if hasattr(computed_caches, 'clear'):
                computed_caches.clear()
        
        result = meal.macro_division
        print(f"\n🏁 Final result: {result}")
        return result is not None
        
    finally:
        # Restore original property
        setattr(Meal, 'macro_division', original_property)

def main():
    """Run None detection and business logic analysis."""
    print("🔍 NONE VALUE DETECTION AND BUSINESS LOGIC ANALYSIS")
    print("=" * 80)
    
    # Test business logic approaches
    test_business_logic_approaches()
    
    # Test with actual meal object and None detection
    success = test_with_none_detection()
    
    print(f"\n📋 CONCLUSIONS:")
    print(f"   1. Current logic is STRICT: ANY None → return None")
    print(f"   2. Alternative PERMISSIVE logic: treat None as 0.0")
    print(f"   3. Actual test result: {'✅ SUCCESS' if success else '❌ NONE DETECTED'}")
    
    print(f"\n💭 BUSINESS DECISION NEEDED:")
    print(f"   Should macro_division be more permissive with partial data?")
    print(f"   - Strict: Requires complete macro data")
    print(f"   - Permissive: Treats missing macros as 0")

if __name__ == "__main__":
    main() 