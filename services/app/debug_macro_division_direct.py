#!/usr/bin/env python3
"""
Debug script to directly test macro_division logic step by step.
"""

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

def manual_macro_division_logic(meal):
    """Manually execute the macro_division logic with detailed debugging."""
    print(f"\n🔍 MANUAL MACRO_DIVISION LOGIC EXECUTION:")
    
    # Step 1: Check not discarded
    try:
        print(f"   Step 1: Calling _check_not_discarded()...")
        meal._check_not_discarded()
        print(f"   ✅ _check_not_discarded() passed")
    except Exception as e:
        print(f"   ❌ _check_not_discarded() failed: {e}")
        return None
    
    # Step 2: Get nutri_facts 
    try:
        print(f"   Step 2: Getting nutri_facts...")
        nutri_facts = meal.nutri_facts
        print(f"   nutri_facts: {nutri_facts}")
        print(f"   nutri_facts is not None: {nutri_facts is not None}")
        print(f"   bool(nutri_facts): {bool(nutri_facts) if nutri_facts else 'nutri_facts is None'}")
        
        if not nutri_facts:
            print(f"   ❌ Returning None because nutri_facts is falsy")
            return None
        print(f"   ✅ nutri_facts exists")
    except Exception as e:
        print(f"   ❌ Error getting nutri_facts: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None
        
    # Step 3: Extract values
    try:
        print(f"   Step 3: Extracting macro values...")
        carb = nutri_facts.carbohydrate.value
        protein = nutri_facts.protein.value
        fat = nutri_facts.total_fat.value
        print(f"   carb: {carb} (type: {type(carb)})")
        print(f"   protein: {protein} (type: {type(protein)})")
        print(f"   fat: {fat} (type: {type(fat)})")
    except Exception as e:
        print(f"   ❌ Error extracting values: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None
        
    # Step 4: Check for None
    try:
        print(f"   Step 4: Checking for None values...")
        if carb is None or protein is None or fat is None:
            print(f"   ❌ One or more values is None")
            return None
        print(f"   ✅ All values are not None")
    except Exception as e:
        print(f"   ❌ Error checking None values: {e}")
        return None
        
    # Step 5: Calculate denominator
    try:
        print(f"   Step 5: Calculating denominator...")
        denominator = carb + protein + fat
        print(f"   denominator: {denominator} (type: {type(denominator)})")
    except Exception as e:
        print(f"   ❌ Error calculating denominator: {e}")
        return None
        
    # Step 6: Check for zero
    try:
        print(f"   Step 6: Checking denominator for zero...")
        if denominator == 0:
            print(f"   ❌ Denominator is zero, returning None")
            return None
        print(f"   ✅ Denominator is not zero")
    except Exception as e:
        print(f"   ❌ Error checking denominator: {e}")
        return None
        
    # Step 7: Create MacroDivision
    try:
        print(f"   Step 7: Creating MacroDivision...")
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
        print(f"   Traceback: {traceback.format_exc()}")
        return None

def compare_manual_vs_property(meal):
    """Compare manual logic execution vs actual property call."""
    print(f"\n🔬 COMPARING MANUAL LOGIC VS PROPERTY CALL:")
    
    # Execute manual logic
    print(f"\n--- MANUAL EXECUTION ---")
    manual_result = manual_macro_division_logic(meal)
    
    # Call actual property
    print(f"\n--- PROPERTY CALL ---")
    try:
        property_result = meal.macro_division
        print(f"   Property result: {property_result}")
    except Exception as e:
        print(f"   ❌ Property call failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        property_result = "ERROR"
    
    # Compare results
    print(f"\n--- COMPARISON ---")
    print(f"   Manual result: {manual_result}")
    print(f"   Property result: {property_result}")
    
    manual_success = manual_result is not None
    property_success = property_result is not None and property_result != "ERROR"
    
    print(f"   Manual success: {manual_success}")
    print(f"   Property success: {property_success}")
    
    if manual_success and not property_success:
        print(f"   🔥 DISCREPANCY: Manual works but property fails!")
    elif not manual_success and property_success:
        print(f"   🔥 DISCREPANCY: Property works but manual fails!")
    elif manual_success and property_success:
        print(f"   ✅ CONSISTENT: Both work")
    else:
        print(f"   ❌ CONSISTENT: Both fail")
    
    return manual_success, property_success

def investigate_nutri_facts_behavior(meal):
    """Specifically investigate nutri_facts behavior."""
    print(f"\n🧪 INVESTIGATING NUTRI_FACTS BEHAVIOR:")
    
    # Call nutri_facts multiple times
    for i in range(3):
        print(f"\n   Call {i+1}:")
        try:
            nutri_facts = meal.nutri_facts
            print(f"     Result: {nutri_facts is not None}")
            if nutri_facts:
                print(f"     Type: {type(nutri_facts)}")
                print(f"     Carb: {nutri_facts.carbohydrate.value}")
                print(f"     Protein: {nutri_facts.protein.value}")
                print(f"     Fat: {nutri_facts.total_fat.value}")
        except Exception as e:
            print(f"     ❌ Error: {e}")

def main():
    """Run comprehensive direct debugging."""
    print("🔍 DIRECT MACRO_DIVISION DEBUGGING")
    print("=" * 80)
    
    # Setup
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
    
    print(f"✅ Created meal and recipe")
    
    # Update meal
    meal.update_properties(recipes=[recipe])
    print(f"✅ Updated meal with recipe")
    
    # Investigate nutri_facts behavior
    investigate_nutri_facts_behavior(meal)
    
    # Compare manual vs property
    manual_success, property_success = compare_manual_vs_property(meal)
    
    print(f"\n📊 FINAL ANALYSIS:")
    if manual_success and not property_success:
        print(f"   🎯 ROOT CAUSE: Issue is in the property implementation itself!")
        print(f"   💡 The logic is correct, but something in the property wrapper is failing.")
    elif not manual_success:
        print(f"   🎯 ROOT CAUSE: Issue is in the underlying logic!")
    else:
        print(f"   🤔 Both manual and property work - issue might be elsewhere.")

if __name__ == "__main__":
    main() 