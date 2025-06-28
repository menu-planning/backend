#!/usr/bin/env python3
"""
Detailed debug script to examine macro_division property behavior.
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

def debug_macro_division_detailed():
    """Debug macro_division with detailed value inspection."""
    print("🔍 Detailed Macro Division Debug")
    
    # Reset state
    reset_all_counters()
    
    # Test case that should work but doesn't: only protein
    calories, carbs, protein, fat = 5000.0, 0.0, 500.0, 0.0
    print(f"\nTesting case: calories={calories}, carbs={carbs}, protein={protein}, fat={fat}")
    
    # Create meal
    meal = create_meal(name="Debug Meal")
    print(f"✅ Created meal: {meal.id}")
    
    # Create recipe with nutrition
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
    print(f"✅ Created recipe with nutrition")
    
    # Check recipe nutrition directly
    print(f"\n📊 Recipe nutrition check:")
    recipe_nutri = recipe.nutri_facts
    if recipe_nutri:
        print(f"  Recipe carbs: {recipe_nutri.carbohydrate.value} (type: {type(recipe_nutri.carbohydrate.value)})")
        print(f"  Recipe protein: {recipe_nutri.protein.value} (type: {type(recipe_nutri.protein.value)})")
        print(f"  Recipe fat: {recipe_nutri.total_fat.value} (type: {type(recipe_nutri.total_fat.value)})")
    else:
        print("  ❌ Recipe nutrition is None")
    
    # Update meal with recipe
    meal.update_properties(recipes=[recipe])
    print(f"✅ Updated meal with recipe")
    
    # Check meal nutrition
    print(f"\n🍽️ Meal nutrition check:")
    meal_nutri = meal.nutri_facts
    if meal_nutri:
        print(f"  Meal carbs: {meal_nutri.carbohydrate.value} (type: {type(meal_nutri.carbohydrate.value)})")
        print(f"  Meal protein: {meal_nutri.protein.value} (type: {type(meal_nutri.protein.value)})")
        print(f"  Meal fat: {meal_nutri.total_fat.value} (type: {type(meal_nutri.total_fat.value)})")
    else:
        print("  ❌ Meal nutrition is None")
        return
    
    # Now debug the macro_division step by step
    print(f"\n🧮 Macro division step-by-step debug:")
    
    # Step 1: Check if nutri_facts exists
    nutri_facts = meal.nutri_facts
    print(f"  Step 1 - nutri_facts exists: {nutri_facts is not None}")
    if not nutri_facts:
        print("  ❌ nutri_facts is None, macro_division will return None")
        return
    
    # Step 2: Extract macro values
    carb_val = nutri_facts.carbohydrate.value
    protein_val = nutri_facts.protein.value
    fat_val = nutri_facts.total_fat.value
    
    print(f"  Step 2 - Extract values:")
    print(f"    carb_val: {carb_val} (type: {type(carb_val)}, is None: {carb_val is None})")
    print(f"    protein_val: {protein_val} (type: {type(protein_val)}, is None: {protein_val is None})")
    print(f"    fat_val: {fat_val} (type: {type(fat_val)}, is None: {fat_val is None})")
    
    # Step 3: Check None condition
    has_none = carb_val is None or protein_val is None or fat_val is None
    print(f"  Step 3 - None check: {has_none}")
    if has_none:
        print("  ❌ One or more values is None, macro_division will return None")
        return
    
    # Step 4: Calculate denominator (safe now since we checked for None)
    assert carb_val is not None and protein_val is not None and fat_val is not None
    denominator = carb_val + protein_val + fat_val
    print(f"  Step 4 - Denominator: {denominator}")
    if denominator == 0:
        print("  ❌ Denominator is zero, macro_division will return None")
        return
    
    # Step 5: Calculate percentages
    carb_pct = (carb_val / denominator) * 100
    protein_pct = (protein_val / denominator) * 100
    fat_pct = (fat_val / denominator) * 100
    
    print(f"  Step 5 - Calculate percentages:")
    print(f"    carb_pct: {carb_pct}")
    print(f"    protein_pct: {protein_pct}")
    print(f"    fat_pct: {fat_pct}")
    print(f"    Total: {carb_pct + protein_pct + fat_pct}")
    
    # Step 6: Call actual macro_division property
    print(f"\n🎯 Actual macro_division property call:")
    actual_macro_div = meal.macro_division
    print(f"  Result: {actual_macro_div}")
    
    if actual_macro_div is None:
        print("  ❌ UNEXPECTED: macro_division returned None despite valid inputs!")
    else:
        print("  ✅ SUCCESS: macro_division returned valid result")
        print(f"    carbohydrate: {actual_macro_div.carbohydrate}")
        print(f"    protein: {actual_macro_div.protein}")
        print(f"    fat: {actual_macro_div.fat}")

if __name__ == "__main__":
    debug_macro_division_detailed() 