#!/usr/bin/env python3
"""
Debug script to trace exactly what happens inside the macro_division property.
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

def debug_macro_division_property(self):
    """Replacement macro_division property with detailed debugging."""
    print(f"\n🔍 INSIDE macro_division property:")
    
    try:
        print(f"   Step 1: Calling _check_not_discarded()...")
        self._check_not_discarded()
        print(f"   ✅ _check_not_discarded() passed")
    except Exception as e:
        print(f"   ❌ _check_not_discarded() failed: {e}")
        return None
    
    try:
        print(f"   Step 2: Checking self.nutri_facts...")
        nutri_facts = self.nutri_facts
        print(f"   nutri_facts result: {nutri_facts is not None}")
        if not nutri_facts:
            print(f"   ❌ Returning None because nutri_facts is falsy")
            return None
        print(f"   ✅ nutri_facts exists")
    except Exception as e:
        print(f"   ❌ Error getting nutri_facts: {e}")
        return None
        
    try:
        print(f"   Step 3: Extracting carb value...")
        carb = nutri_facts.carbohydrate.value
        print(f"   carb: {carb} (type: {type(carb)})")
    except Exception as e:
        print(f"   ❌ Error getting carb value: {e}")
        return None
        
    try:
        print(f"   Step 4: Extracting protein value...")
        protein = nutri_facts.protein.value
        print(f"   protein: {protein} (type: {type(protein)})")
    except Exception as e:
        print(f"   ❌ Error getting protein value: {e}")
        return None
        
    try:
        print(f"   Step 5: Extracting fat value...")
        fat = nutri_facts.total_fat.value
        print(f"   fat: {fat} (type: {type(fat)})")
    except Exception as e:
        print(f"   ❌ Error getting fat value: {e}")
        return None
        
    try:
        print(f"   Step 6: Checking for None values...")
        if carb is None or protein is None or fat is None:
            print(f"   ❌ One or more values is None: carb={carb}, protein={protein}, fat={fat}")
            return None
        print(f"   ✅ All values are not None")
    except Exception as e:
        print(f"   ❌ Error checking None values: {e}")
        return None
        
    try:
        print(f"   Step 7: Calculating denominator...")
        denominator = carb + protein + fat
        print(f"   denominator: {denominator} (type: {type(denominator)})")
    except Exception as e:
        print(f"   ❌ Error calculating denominator: {e}")
        return None
        
    try:
        print(f"   Step 8: Checking denominator for zero...")
        if denominator == 0:
            print(f"   ❌ Denominator is zero, returning None")
            return None
        print(f"   ✅ Denominator is not zero")
    except Exception as e:
        print(f"   ❌ Error checking denominator: {e}")
        return None
        
    try:
        print(f"   Step 9: Creating MacroDivision object...")
        carb_percent = (carb / denominator) * 100
        protein_percent = (protein / denominator) * 100
        fat_percent = (fat / denominator) * 100
        print(f"   Percentages: carb={carb_percent}, protein={protein_percent}, fat={fat_percent}")
        
        result = MacroDivision(
            carbohydrate=carb_percent,
            protein=protein_percent,
            fat=fat_percent,
        )
        print(f"   ✅ Created MacroDivision: {result}")
        return result
    except Exception as e:
        print(f"   ❌ Error creating MacroDivision: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return None

def patch_macro_division_property():
    """Patch the macro_division property to add debugging."""
    print("🔧 Patching macro_division property for debugging...")
    
    # Replace the property with our debug version
    original_property = Meal.macro_division
    debug_property = functools.cached_property(debug_macro_division_property)
    setattr(Meal, 'macro_division', debug_property)
    
    print("✅ Macro division property patched")
    return original_property

def restore_macro_division_property(original_property):
    """Restore the original macro_division property."""
    setattr(Meal, 'macro_division', original_property)
    print("✅ Macro division property restored")

def test_with_patched_property():
    """Test macro_division with our debug-enabled property."""
    print("🧪 TESTING WITH PATCHED MACRO_DIVISION PROPERTY")
    print("=" * 70)
    
    # Reset state
    reset_meal_domain_counters()
    reset_recipe_domain_counters()
    reset_tag_domain_counters()
    
    # Patch the property
    original = patch_macro_division_property()
    
    try:
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
        
        # Update meal
        meal.update_properties(recipes=[recipe])
        
        print(f"\n🎯 About to call macro_division property...")
        result = meal.macro_division
        print(f"\n🏁 Final result: {result}")
        
        return result is not None
        
    finally:
        # Always restore the original property
        restore_macro_division_property(original)

def main():
    """Run the detailed internal debugging."""
    print("🔍 DEBUGGING MACRO_DIVISION PROPERTY INTERNALS")
    print("=" * 80)
    
    success = test_with_patched_property()
    
    print(f"\n📊 RESULT: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    if not success:
        print("\n💡 The issue is inside the macro_division property implementation!")
    else:
        print("\n🤔 The patched version worked - investigation continues...")

if __name__ == "__main__":
    main() 