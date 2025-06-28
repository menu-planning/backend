#!/usr/bin/env python3

# Temporary debug script to understand nutrition issue

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_domain_factories import create_meal
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.recipe.recipe_domain_factories import create_recipe_kwargs

def create_recipe_for_meal(meal_id: str, author_id: str, **recipe_kwargs):
    """Helper to create recipe with correct meal_id and author_id."""
    kwargs = create_recipe_kwargs(
        meal_id=meal_id,
        author_id=author_id,
        **recipe_kwargs
    )
    from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
    return _Recipe(**kwargs)

def debug_nutrition():
    # Test case: (10000.0, 1000.0, 1000.0, 1000.0) - extremely high nutrition
    calories, carbs, protein, fat = 10000.0, 1000.0, 1000.0, 1000.0
    
    meal = create_meal(name="Debug Nutrition Meal")
    
    # Create a recipe with extreme nutrition
    recipe = create_recipe_for_meal(
        meal_id=meal.id,
        author_id=meal.author_id,
        name="Debug Nutrition Recipe",
        nutri_facts=NutriFacts(
            calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM)
        )
    )
    
    meal.update_properties(recipes=[recipe])
    
    print(f"Meal nutrition: {meal.nutri_facts}")
    if meal.nutri_facts:
        print(f"Calories: {meal.nutri_facts.calories}")
        print(f"Carbs: {meal.nutri_facts.carbohydrate}")
        print(f"Protein: {meal.nutri_facts.protein}")
        print(f"Fat: {meal.nutri_facts.total_fat}")
        
        if meal.nutri_facts.carbohydrate:
            print(f"Carbs value: {meal.nutri_facts.carbohydrate.value}")
        if meal.nutri_facts.protein:
            print(f"Protein value: {meal.nutri_facts.protein.value}")
        if meal.nutri_facts.total_fat:
            print(f"Fat value: {meal.nutri_facts.total_fat.value}")
    
    print(f"Macro division: {meal.macro_division}")

if __name__ == "__main__":
    debug_nutrition() 