from __future__ import annotations

"""
Data factories for ApiMeal benchmark testing following seedwork patterns.
Uses deterministic values (not random) for consistent benchmark behavior.

This module provides:
- Deterministic data creation with static counters
- Performance test scenarios for benchmarking
- API-specific factory functions for schema validation
- Both simple and complex meal configurations

All data follows the exact structure of ApiMeal schemas and their relationships.
Uses check_missing_attributes from utils.py for complete data validation.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Type
import uuid

from pydantic import BaseModel

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.enums import MeasureUnit

# Import ApiIngredient for proper ingredient creation
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient

# Domain and ORM imports for conversion testing
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.shared_kernel.domain.value_objects.tag import Tag



# Use check_missing_attributes from utils like random_refs.py does  
from tests.contexts.recipes_catalog.data_factories.meal.meal_domain_factories import create_meal_kwargs
from tests.contexts.recipes_catalog.data_factories.meal.meal_orm_factories import create_meal_orm_kwargs
from tests.contexts.recipes_catalog.data_factories.recipe.recipe_domain_factories import create_recipe
from tests.contexts.recipes_catalog.data_factories.recipe.recipe_orm_factories import create_recipe_orm

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_MEAL_COUNTER = 1
_RECIPE_COUNTER = 1
_TAG_COUNTER = 1

# Add new counters for the new factories
_RATING_COUNTER = 1
_INGREDIENT_COUNTER = 1
_USER_COUNTER = 1
_ROLE_COUNTER = 1
_MENU_MEAL_COUNTER = 1
_MENU_COUNTER = 1
_CLIENT_COUNTER = 1


def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _MEAL_COUNTER, _RECIPE_COUNTER, _TAG_COUNTER, _RATING_COUNTER, _INGREDIENT_COUNTER, _USER_COUNTER, _ROLE_COUNTER, _MENU_MEAL_COUNTER, _MENU_COUNTER, _CLIENT_COUNTER
    _MEAL_COUNTER = 1
    _RECIPE_COUNTER = 1
    _TAG_COUNTER = 1
    _RATING_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _USER_COUNTER = 1
    _ROLE_COUNTER = 1
    _MENU_MEAL_COUNTER = 1
    _MENU_COUNTER = 1
    _CLIENT_COUNTER = 1


# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

# Realistic recipe data sets
REALISTIC_RECIPES = [
    {
        "name": "Classic Spaghetti Carbonara",
        "description": "Traditional Roman pasta dish with eggs, cheese, pancetta, and black pepper. Creamy without cream, this authentic recipe delivers rich, comforting flavors.",
        "instructions": [
            "Bring a large pot of salted water to boil for the pasta",
            "Cut 200g pancetta into small cubes and cook in a large skillet over medium heat until crispy (about 5-7 minutes)",
            "In a bowl, whisk together 3 large eggs, 100g grated Pecorino Romano, and plenty of freshly cracked black pepper",
            "Cook 400g spaghetti according to package directions until al dente, reserving 1 cup pasta water before draining",
            "Remove pancetta from heat and immediately add hot, drained pasta to the skillet",
            "Quickly toss pasta with pancetta, then remove from heat completely",
            "Slowly pour egg mixture over pasta while tossing continuously to create a creamy sauce (don't scramble the eggs!)",
            "Add pasta water gradually if needed to achieve creamy consistency",
            "Serve immediately with extra Pecorino Romano and black pepper"
        ],
        "ingredients": [
            {"name": "spaghetti", "quantity": 400, "unit": "g"},
            {"name": "pancetta", "quantity": 200, "unit": "g"},
            {"name": "large eggs", "quantity": 3, "unit": "pieces"},
            {"name": "Pecorino Romano cheese", "quantity": 100, "unit": "g"},
            {"name": "black pepper", "quantity": 2, "unit": "tsp"},
            {"name": "salt", "quantity": 1, "unit": "tsp"}
        ],
        "utensils": "Large pot, large skillet, whisk, tongs, cheese grater, measuring cups",
        "total_time": 25,
        "cuisine": "italian",
        "difficulty": "medium",
        "calories": 520,
        "protein": 22.0,
        "carbs": 58.0,
        "fat": 21.0
    },
    {
        "name": "Thai Green Curry Chicken",
        "description": "Aromatic Thai curry with tender chicken, vegetables, and fresh herbs in rich coconut milk. Spicy, fragrant, and deeply satisfying.",
        "instructions": [
            "Heat 2 tbsp coconut oil in a large wok or deep skillet over medium-high heat",
            "Add 3 tbsp green curry paste and stir-fry for 1-2 minutes until fragrant",
            "Pour in the thick part of 1 can coconut milk (about 1/2 cup) and simmer until oil separates",
            "Add 500g diced chicken thigh and cook until nearly done (about 8 minutes)",
            "Add remaining coconut milk, 2 tbsp fish sauce, 1 tbsp brown sugar, and Thai basil leaves",
            "Add sliced bell peppers, baby eggplants, and bamboo shoots",
            "Simmer for 10-15 minutes until vegetables are tender and chicken is cooked through",
            "Taste and adjust seasoning with more fish sauce, sugar, or curry paste as needed",
            "Garnish with fresh Thai basil, sliced red chilies, and serve with jasmine rice"
        ],
        "ingredients": [
            {"name": "chicken thigh", "quantity": 500, "unit": "g"},
            {"name": "coconut milk", "quantity": 400, "unit": "ml"},
            {"name": "green curry paste", "quantity": 3, "unit": "tbsp"},
            {"name": "fish sauce", "quantity": 2, "unit": "tbsp"},
            {"name": "brown sugar", "quantity": 1, "unit": "tbsp"},
            {"name": "bell peppers", "quantity": 2, "unit": "pieces"},
            {"name": "baby eggplants", "quantity": 150, "unit": "g"},
            {"name": "bamboo shoots", "quantity": 100, "unit": "g"},
            {"name": "Thai basil", "quantity": 30, "unit": "g"},
            {"name": "red chilies", "quantity": 2, "unit": "pieces"},
            {"name": "coconut oil", "quantity": 2, "unit": "tbsp"}
        ],
        "utensils": "Large wok or deep skillet, wooden spoon, knife, cutting board",
        "total_time": 35,
        "cuisine": "asian",
        "difficulty": "medium",
        "calories": 380,
        "protein": 28.0,
        "carbs": 12.0,
        "fat": 26.0
    },
    {
        "name": "Mediterranean Quinoa Bowl",
        "description": "Nutritious and colorful bowl with fluffy quinoa, roasted vegetables, feta cheese, and tahini dressing. Perfect for healthy lunch or dinner.",
        "instructions": [
            "Preheat oven to 220°C (425°F)",
            "Rinse 1 cup quinoa until water runs clear, then cook in 2 cups vegetable broth for 15 minutes",
            "Dice zucchini, bell peppers, and red onion into 2cm pieces",
            "Toss vegetables with 2 tbsp olive oil, salt, pepper, and dried oregano",
            "Roast vegetables for 20-25 minutes until tender and lightly caramelized",
            "For tahini dressing: whisk together 3 tbsp tahini, 2 tbsp lemon juice, 1 tbsp olive oil, and 2-3 tbsp water",
            "Season dressing with salt, pepper, and a pinch of garlic powder",
            "Fluff cooked quinoa with a fork and let cool slightly",
            "Assemble bowls with quinoa base, roasted vegetables, cherry tomatoes, cucumber, and crumbled feta",
            "Drizzle with tahini dressing and garnish with fresh parsley and pine nuts"
        ],
        "ingredients": [
            {"name": "quinoa", "quantity": 1, "unit": "cup"},
            {"name": "vegetable broth", "quantity": 2, "unit": "cups"},
            {"name": "zucchini", "quantity": 1, "unit": "piece"},
            {"name": "bell pepper", "quantity": 1, "unit": "piece"},
            {"name": "red onion", "quantity": 0.5, "unit": "piece"},
            {"name": "cherry tomatoes", "quantity": 200, "unit": "g"},
            {"name": "cucumber", "quantity": 1, "unit": "piece"},
            {"name": "feta cheese", "quantity": 100, "unit": "g"},
            {"name": "tahini", "quantity": 3, "unit": "tbsp"},
            {"name": "lemon juice", "quantity": 2, "unit": "tbsp"},
            {"name": "olive oil", "quantity": 3, "unit": "tbsp"},
            {"name": "fresh parsley", "quantity": 20, "unit": "g"},
            {"name": "pine nuts", "quantity": 30, "unit": "g"},
            {"name": "dried oregano", "quantity": 1, "unit": "tsp"}
        ],
        "utensils": "Large baking sheet, saucepan, whisk, knife, cutting board, serving bowls",
        "total_time": 45,
        "cuisine": "mediterranean",
        "difficulty": "easy",
        "calories": 420,
        "protein": 16.0,
        "carbs": 45.0,
        "fat": 22.0
    },
    {
        "name": "Beef and Mushroom Stroganoff",
        "description": "Classic comfort food with tender beef strips, earthy mushrooms, and rich sour cream sauce served over egg noodles.",
        "instructions": [
            "Slice 600g beef sirloin into thin strips against the grain",
            "Season beef with salt and pepper, then dredge lightly in flour",
            "Heat 2 tbsp oil in large skillet over medium-high heat",
            "Sear beef in batches until browned (about 2-3 minutes per batch), remove and set aside",
            "In same skillet, add sliced mushrooms and cook until golden (about 5 minutes)",
            "Add diced onion and minced garlic, cook until softened (3-4 minutes)",
            "Pour in beef broth and bring to simmer, scraping up browned bits",
            "Return beef to skillet and simmer for 15-20 minutes until tender",
            "Reduce heat to low and stir in sour cream, Dijon mustard, and fresh dill",
            "Cook for 2-3 more minutes without boiling (to prevent curdling)",
            "Serve over cooked egg noodles with extra dill and black pepper"
        ],
        "ingredients": [
            {"name": "beef sirloin", "quantity": 600, "unit": "g"},
            {"name": "mushrooms", "quantity": 300, "unit": "g"},
            {"name": "egg noodles", "quantity": 400, "unit": "g"},
            {"name": "sour cream", "quantity": 200, "unit": "ml"},
            {"name": "beef broth", "quantity": 2, "unit": "cups"},
            {"name": "onion", "quantity": 1, "unit": "piece"},
            {"name": "garlic", "quantity": 3, "unit": "cloves"},
            {"name": "flour", "quantity": 2, "unit": "tbsp"},
            {"name": "Dijon mustard", "quantity": 1, "unit": "tbsp"},
            {"name": "fresh dill", "quantity": 15, "unit": "g"},
            {"name": "vegetable oil", "quantity": 2, "unit": "tbsp"}
        ],
        "utensils": "Large skillet, large pot for noodles, tongs, wooden spoon",
        "total_time": 50,
        "cuisine": "american",
        "difficulty": "medium",
        "calories": 485,
        "protein": 32.0,
        "carbs": 38.0,
        "fat": 24.0
    },
    {
        "name": "Chocolate Lava Cake",
        "description": "Decadent individual chocolate cakes with molten chocolate centers. Perfect for special occasions or when you need an impressive dessert.",
        "instructions": [
            "Preheat oven to 220°C (425°F) and generously butter 4 ramekins",
            "Dust ramekins with cocoa powder, tapping out excess",
            "Melt 100g dark chocolate and 100g butter in double boiler until smooth",
            "In a bowl, whisk 2 whole eggs and 2 egg yolks with 60g sugar until thick and pale",
            "Slowly whisk melted chocolate mixture into egg mixture",
            "Fold in 30g flour and pinch of salt until just combined (don't overmix)",
            "Divide batter evenly among prepared ramekins",
            "Bake for 12-14 minutes until edges are firm but centers still jiggle slightly",
            "Let rest for 1 minute, then run knife around edges",
            "Invert onto serving plates and let sit 10 seconds before lifting ramekins",
            "Dust with powdered sugar and serve immediately with vanilla ice cream"
        ],
        "ingredients": [
            {"name": "dark chocolate", "quantity": 100, "unit": "g"},
            {"name": "butter", "quantity": 100, "unit": "g"},
            {"name": "eggs", "quantity": 2, "unit": "pieces"},
            {"name": "egg yolks", "quantity": 2, "unit": "pieces"},
            {"name": "sugar", "quantity": 60, "unit": "g"},
            {"name": "flour", "quantity": 30, "unit": "g"},
            {"name": "cocoa powder", "quantity": 1, "unit": "tbsp"},
            {"name": "salt", "quantity": 0.25, "unit": "tsp"},
            {"name": "powdered sugar", "quantity": 2, "unit": "tbsp"}
        ],
        "utensils": "4 ramekins, double boiler, whisk, mixing bowls, sieve",
        "total_time": 30,
        "cuisine": "french",
        "difficulty": "hard",
        "calories": 320,
        "protein": 8.0,
        "carbs": 28.0,
        "fat": 22.0
    }
]

REALISTIC_MEALS = [
    {
        "name": "Italian Date Night Dinner",
        "description": "Romantic three-course Italian meal perfect for special occasions. Features classic carbonara with wine pairing suggestions.",
        "recipes": [0],  # Carbonara
        "tags": ["dinner", "italian", "romantic", "date-night"]
    },
    {
        "name": "Asian Fusion Feast",
        "description": "Spicy and aromatic Thai-inspired meal with balanced flavors and fresh ingredients. Great for adventurous eaters.",
        "recipes": [1],  # Thai curry
        "tags": ["dinner", "asian", "spicy", "healthy"]
    },
    {
        "name": "Healthy Mediterranean Lunch",
        "description": "Light, nutritious meal packed with vegetables, quinoa, and Mediterranean flavors. Perfect for meal prep.",
        "recipes": [2],  # Quinoa bowl
        "tags": ["lunch", "mediterranean", "vegetarian", "healthy", "meal-prep"]
    },
    {
        "name": "Comfort Food Evening",
        "description": "Hearty, satisfying meal perfect for cold evenings. Classic stroganoff with rich, creamy sauce.",
        "recipes": [3],  # Stroganoff
        "tags": ["dinner", "comfort-food", "american", "hearty"]
    },
    {
        "name": "Elegant Dessert Experience",
        "description": "Sophisticated chocolate dessert that's sure to impress. Restaurant-quality presentation at home.",
        "recipes": [4],  # Lava cake
        "tags": ["dessert", "chocolate", "french", "elegant", "special-occasion"]
    },
    {
        "name": "Weekend Dinner Party Menu",
        "description": "Complete dinner party menu with appetizer-style quinoa bowl, hearty main course, and show-stopping dessert.",
        "recipes": [2, 3, 4],  # Quinoa bowl, stroganoff, lava cake
        "tags": ["dinner", "entertaining", "multi-course", "impressive"]
    }
]

# =============================================================================
# API MEAL DATA FACTORIES
# =============================================================================

def create_api_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create API meal kwargs with deterministic values.
    
    Following seedwork pattern with static counters for consistent benchmark behavior.
    All required API schema attributes are guaranteed to be present.
    Uses check_missing_attributes to ensure completeness.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required API meal creation parameters
    """
    global _MEAL_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Use realistic meal data if available
    meal_index = (_MEAL_COUNTER - 1) % len(REALISTIC_MEALS)
    realistic_meal = REALISTIC_MEALS[meal_index]
    
    # Generate dummy nutritional facts for computed properties
    nutri_facts = None
    if _MEAL_COUNTER % 3 == 0:  # Add nutri_facts to every 3rd meal
        nutri_facts = ApiNutriFacts(
            calories=float(500 + (_MEAL_COUNTER % 500)),
            protein=float(20 + (_MEAL_COUNTER % 30)),
            carbohydrate=float(50 + (_MEAL_COUNTER % 50)),
            total_fat=float(10 + (_MEAL_COUNTER % 20)),
            saturated_fat=float(3 + (_MEAL_COUNTER % 7)),
            trans_fat=float(0.1 + (_MEAL_COUNTER % 1)),
            sugar=float(5 + (_MEAL_COUNTER % 15)),
            sodium=float(800 + (_MEAL_COUNTER % 400))
        ) # type: ignore
    
    final_kwargs = {
        "id": kwargs.get("id", f"meal_{_MEAL_COUNTER:03d}"),
        "name": kwargs.get("name", realistic_meal["name"]),
        "author_id": kwargs.get("author_id", f"author_{(_MEAL_COUNTER % 5) + 1}"),
        "menu_id": kwargs.get("menu_id", None),
        "recipes": kwargs.get("recipes", []),
        "tags": kwargs.get("tags", frozenset()),  # Use frozenset for hashable tags
        "description": kwargs.get("description", realistic_meal["description"]),
        "notes": kwargs.get("notes", f"Chef's notes: This {realistic_meal['name'].lower()} is perfect for {', '.join(realistic_meal['tags'][:2])}. Consider pairing with a nice wine."),
        "like": kwargs.get("like", _MEAL_COUNTER % 3 == 0),
        "image_url": kwargs.get("image_url", f"https://example.com/meal_{_MEAL_COUNTER}.jpg" if _MEAL_COUNTER % 2 == 0 else None),
        # Computed properties - provide dummy data that complies with constraints
        "nutri_facts": kwargs.get("nutri_facts", nutri_facts),
        "weight_in_grams": kwargs.get("weight_in_grams", 400 + (_MEAL_COUNTER % 600) if _MEAL_COUNTER % 2 == 0 else None),
        "calorie_density": kwargs.get("calorie_density", 1.5 + (_MEAL_COUNTER % 3) * 0.5 if _MEAL_COUNTER % 3 == 0 else None),
        "carbo_percentage": kwargs.get("carbo_percentage", 45.0 + (_MEAL_COUNTER % 20) if _MEAL_COUNTER % 2 == 0 else None),
        "protein_percentage": kwargs.get("protein_percentage", 15.0 + (_MEAL_COUNTER % 25) if _MEAL_COUNTER % 3 == 0 else None),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 20.0 + (_MEAL_COUNTER % 30) if _MEAL_COUNTER % 4 == 0 else None),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MEAL_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MEAL_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Check for missing attributes using Pydantic-specific check
    missing = check_missing_pydantic_fields(ApiMeal, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
    return final_kwargs


def create_api_meal(**kwargs) -> ApiMeal:
    """
    Create an ApiMeal instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiMeal instance
    """
    meal_kwargs = create_api_meal_kwargs(**kwargs)
    return ApiMeal(**meal_kwargs)


# =============================================================================
# API RECIPE DATA FACTORIES
# =============================================================================

def create_api_recipe_data(**kwargs) -> Dict[str, Any]:
    """
    Create API recipe data with deterministic values.
    Uses check_missing_attributes to ensure completeness.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with recipe creation parameters
    """
    global _RECIPE_COUNTER
    
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Use realistic recipe data if available
    recipe_index = (_RECIPE_COUNTER - 1) % len(REALISTIC_RECIPES)
    realistic_recipe = REALISTIC_RECIPES[recipe_index]
    
    # Generate proper image_url - use proper string value or None
    image_url = None
    if _RECIPE_COUNTER % 2 == 0:
        image_url = f"https://example.com/recipe_{_RECIPE_COUNTER}.jpg"
    
    # Create realistic nutritional facts based on recipe data
    nutri_facts = None
    if realistic_recipe.get("calories"):
        nutri_facts = ApiNutriFacts(
            calories=float(realistic_recipe["calories"]),
            protein=float(realistic_recipe["protein"]),
            carbohydrate=float(realistic_recipe["carbs"]),
            total_fat=float(realistic_recipe["fat"]),
            saturated_fat=float(realistic_recipe["fat"] * 0.3),  # Estimate 30% saturated
            trans_fat=0.1,
            sugar=float(realistic_recipe["carbs"] * 0.15),  # Estimate 15% sugar
            sodium=800.0 + (_RECIPE_COUNTER % 400)  # Varied sodium content
        ) # type: ignore
    
    # Convert realistic ingredients to proper ApiIngredient objects
    ingredients_list = []
    for i, ingredient in enumerate(realistic_recipe.get("ingredients", [])):
        api_ingredient = ApiIngredient(
            name=ingredient["name"],
            quantity=float(ingredient["quantity"]),
            unit=_get_measure_unit_from_string(ingredient["unit"]),
            position=i,
            full_text=f"{ingredient['quantity']} {ingredient['unit']} {ingredient['name']}",
            product_id=None  # No product linking in test data
        )
        ingredients_list.append(api_ingredient)
    
    # Join instructions into a single string (API schema expects string, not list)
    instructions_text = ". ".join(realistic_recipe.get("instructions", [f"Step {i+1} for {realistic_recipe['name']}" for i in range(3)]))
    
    final_kwargs = {
        "id": kwargs.get("id", f"recipe_{_RECIPE_COUNTER:03d}"),
        "name": kwargs.get("name", realistic_recipe["name"]),
        "meal_id": kwargs.get("meal_id", f"meal_{(_RECIPE_COUNTER % 10) + 1:03d}"),  # Provide valid meal_id
        "author_id": kwargs.get("author_id", f"author_{(_RECIPE_COUNTER % 5) + 1}"),
        "description": kwargs.get("description", realistic_recipe["description"]),
        "instructions": kwargs.get("instructions", instructions_text),
        "ingredients": kwargs.get("ingredients", ingredients_list),
        "tags": kwargs.get("tags", frozenset()),  # Use frozenset for hashable tags
        "utensils": kwargs.get("utensils", realistic_recipe.get("utensils", f"Basic kitchen tools for {realistic_recipe['name']}")),
        "total_time": kwargs.get("total_time", realistic_recipe.get("total_time", 30 + (_RECIPE_COUNTER % 60))),
        "notes": kwargs.get("notes", f"Chef's tip: This {realistic_recipe['name'].lower()} works great for {realistic_recipe.get('difficulty', 'medium')} level cooks. {realistic_recipe.get('cuisine', 'international').title()} cuisine at its finest."),
        "privacy": kwargs.get("privacy", Privacy.PRIVATE),  # Use Privacy enum directly
        "nutri_facts": kwargs.get("nutri_facts", nutri_facts),
        "weight_in_grams": kwargs.get("weight_in_grams", 300 + (_RECIPE_COUNTER % 300)),
        "image_url": kwargs.get("image_url", image_url),  # Use proper string value
        "ratings": kwargs.get("ratings", []),
        # Computed properties - provide dummy data that complies with constraints (0-5 range)
        "average_taste_rating": kwargs.get("average_taste_rating", 3.0 + (_RECIPE_COUNTER % 3) * 0.5 if _RECIPE_COUNTER % 2 == 0 else None),
        "average_convenience_rating": kwargs.get("average_convenience_rating", 2.5 + (_RECIPE_COUNTER % 4) * 0.5 if _RECIPE_COUNTER % 3 == 0 else None),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_RECIPE_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_RECIPE_COUNTER, minutes=15)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Check for missing attributes using Pydantic-specific check
    missing = check_missing_pydantic_fields(ApiRecipe, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"

    _RECIPE_COUNTER += 1
    return final_kwargs


def create_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create an ApiRecipe instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe instance
    """
    recipe_data = create_api_recipe_data(**kwargs)
    return ApiRecipe(**recipe_data)


# =============================================================================
# API TAG DATA FACTORIES
# =============================================================================

def create_api_tag_data(**kwargs) -> Dict[str, Any]:
    """
    Create API tag data with deterministic values.
    Uses check_missing_attributes to ensure completeness.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # More realistic tag combinations based on our recipe data
    realistic_tags = [
        {"key": "cuisine", "value": "italian"},
        {"key": "difficulty", "value": "medium"},
        {"key": "meal-type", "value": "dinner"},
        {"key": "diet", "value": "vegetarian"},
        {"key": "cuisine", "value": "asian"},
        {"key": "dietary", "value": "spicy"},
        {"key": "lifestyle", "value": "healthy"},
        {"key": "cuisine", "value": "mediterranean"},
        {"key": "meal-type", "value": "lunch"},
        {"key": "prep-style", "value": "meal-prep"},
        {"key": "mood", "value": "comfort-food"},
        {"key": "cuisine", "value": "american"},
        {"key": "difficulty", "value": "easy"},
        {"key": "occasion", "value": "date-night"},
        {"key": "meal-type", "value": "dessert"},
        {"key": "cuisine", "value": "french"},
        {"key": "mood", "value": "elegant"},
        {"key": "occasion", "value": "special-occasion"},
        {"key": "style", "value": "entertaining"},
        {"key": "complexity", "value": "multi-course"}
    ]
    
    tag_index = (_TAG_COUNTER - 1) % len(realistic_tags)
    realistic_tag = realistic_tags[tag_index]
    
    final_kwargs = {
        "key": kwargs.get("key", realistic_tag["key"]),
        "value": kwargs.get("value", realistic_tag["value"]),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", "meal"),
    }
    
    # Check for missing attributes using Pydantic-specific check
    missing = check_missing_pydantic_fields(ApiTag, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    
    _TAG_COUNTER += 1
    return final_kwargs


def create_api_tag(**kwargs) -> ApiTag:
    """
    Create an ApiTag instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiTag instance
    """
    tag_data = create_api_tag_data(**kwargs)
    return ApiTag(**tag_data)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_api_meal_with_recipes(recipe_count: int = 3, **kwargs) -> ApiMeal:
    """
    Create an ApiMeal with a specified number of recipes.
    
    Args:
        recipe_count: Number of recipes to include
        **kwargs: Override any default values
        
    Returns:
        ApiMeal with recipes
    """
    # Create recipes first
    recipes = []
    for i in range(recipe_count):
        recipe = create_api_recipe()
        recipes.append(recipe)
    
    # Create meal with recipes
    meal_kwargs = create_api_meal_kwargs(**kwargs)
    meal_kwargs["recipes"] = recipes
    return ApiMeal(**meal_kwargs)


def create_api_meal_with_tags(tag_count: int = 2, **kwargs) -> ApiMeal:
    """
    Create an ApiMeal with a specified number of tags.
    
    Args:
        tag_count: Number of tags to include
        **kwargs: Override any default values
        
    Returns:
        ApiMeal with tags
    """
    # Create tags first - using frozenset for hashable tags
    tags = frozenset(create_api_tag() for _ in range(tag_count))
    
    # Create meal with tags
    meal_kwargs = create_api_meal_kwargs(**kwargs)
    meal_kwargs["tags"] = tags
    return ApiMeal(**meal_kwargs)


def create_complex_api_meal(**kwargs) -> ApiMeal:
    """
    Create a complex ApiMeal with all optional fields populated.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Complex ApiMeal instance
    """
    # Create comprehensive nutritional facts if not provided
    if "nutri_facts" not in kwargs:
        kwargs["nutri_facts"] = ApiNutriFacts(
            calories=kwargs.get("calories", 800.0),
            protein=kwargs.get("protein", 50.0),
            carbohydrate=kwargs.get("carbohydrate", 90.0),
            total_fat=kwargs.get("total_fat", 27.0),
            saturated_fat=kwargs.get("saturated_fat", 8.0),
            trans_fat=kwargs.get("trans_fat", 0.1),
            sugar=kwargs.get("sugar", 15.0),
            sodium=kwargs.get("sodium", 1200.0)
        ) # type: ignore
    
    # Create realistic recipes with complex data
    recipes = []
    for i in range(kwargs.get("recipe_count", 3)):
        recipe = create_api_recipe()
        recipes.append(recipe)
    
    # Create realistic tag combinations - using TagFrozensetAdapter for proper frozenset creation
    realistic_tag_sets = [
        ["cuisine:italian", "difficulty:medium", "meal-type:dinner", "occasion:date-night"],
        ["cuisine:asian", "dietary:spicy", "lifestyle:healthy", "meal-type:dinner"],
        ["cuisine:mediterranean", "diet:vegetarian", "lifestyle:healthy", "prep-style:meal-prep"],
        ["mood:comfort-food", "cuisine:american", "difficulty:easy", "meal-type:dinner"],
        ["cuisine:french", "mood:elegant", "occasion:special-occasion", "meal-type:dessert"]
    ]
    
    tag_set_index = _MEAL_COUNTER % len(realistic_tag_sets)
    tag_strings = realistic_tag_sets[tag_set_index]
    
    # Create domain tags first (which are hashable), then convert to ApiTag frozenset
    domain_tags = []
    for tag_string in tag_strings:
        key, value = tag_string.split(":")
        domain_tag = Tag(key=key, value=value, author_id="author_1", type="meal")
        domain_tags.append(domain_tag)
    
    api_tags = frozenset(ApiTag.from_domain(tag) for tag in domain_tags)
    
    # Create complex meal with all computed properties filled
    meal_kwargs = create_api_meal_kwargs(
        description="Multi-course gourmet meal featuring authentic techniques and premium ingredients. Perfect for entertaining or special occasions.",
        notes="This complex meal showcases advanced culinary techniques and flavor combinations. Allow extra time for preparation and consider prep work ahead of time. Wine pairing recommendations available upon request.",
        like=True,
        image_url="https://example.com/complex-gourmet-meal.jpg",
        # Ensure all computed properties have values (not None)
        weight_in_grams=800,
        calorie_density=2.5,
        carbo_percentage=55.0,
        protein_percentage=25.0,
        total_fat_percentage=20.0,
        recipes=recipes,
        tags=api_tags,
        **{k: v for k, v in kwargs.items() if k not in ["recipe_count", "tag_count", "calories", "protein", "carbohydrate", "total_fat", "saturated_fat", "trans_fat", "sugar", "sodium"]}
    )
    
    return ApiMeal(**meal_kwargs)


# =============================================================================
# PERFORMANCE TEST SCENARIOS
# =============================================================================

def create_api_meal_performance_scenarios() -> List[Dict[str, Any]]:
    """
    Create predefined performance test scenarios.
    
    Returns:
        List of performance test scenarios with data and expectations
    """
    scenarios = []
    
    # Scenario 1: Minimal meal
    scenarios.append({
        "scenario_id": "minimal_meal",
        "meal_data": create_api_meal_kwargs(recipes=[], tags=frozenset()),
        "max_time_seconds": 0.001,
        "expected_recipe_count": 0,
        "expected_tag_count": 0,
        "description": "Minimal meal with no recipes or tags"
    })
    
    # Scenario 2: Standard meal with realistic complex recipes
    recipes = [ApiRecipe(**create_api_recipe_data()) for _ in range(3)]
    # Use TagFrozensetAdapter for proper tag frozenset creation
    tag_data_list = [create_api_tag_data() for _ in range(2)]
    tags = frozenset(ApiTag(**tag_data) for tag_data in tag_data_list)
    scenarios.append({
        "scenario_id": "standard_meal_realistic",
        "meal_data": create_api_meal_kwargs(recipes=recipes, tags=tags),
        "max_time_seconds": 0.003,
        "expected_recipe_count": 3,
        "expected_tag_count": 2,
        "description": "Standard meal with 3 complex recipes and 2 realistic tags"
    })
    
    # Scenario 3: Large meal with production-like complexity
    recipes = [ApiRecipe(**create_api_recipe_data()) for _ in range(10)]
    # Use TagFrozensetAdapter for proper tag frozenset creation
    tag_data_list = [create_api_tag_data() for _ in range(5)]
    tags = frozenset(ApiTag(**tag_data) for tag_data in tag_data_list)
    scenarios.append({
        "scenario_id": "large_meal_complex",
        "meal_data": create_api_meal_kwargs(recipes=recipes, tags=tags),
        "max_time_seconds": 0.005,
        "expected_recipe_count": 10,
        "expected_tag_count": 5,
        "description": "Large meal with 10 complex recipes and 5 realistic tags"
    })
    
    # Scenario 4: Gourmet meal with full nutritional complexity
    nutri_facts = ApiNutriFacts(
        calories=800.0, protein=50.0, carbohydrate=90.0, total_fat=27.0,
        saturated_fat=8.0, trans_fat=0.1, sugar=15.0, sodium=1200.0
    ) # type: ignore
    recipes = [ApiRecipe(**create_api_recipe_data()) for _ in range(5)]
    # Create realistic gourmet tags using domain objects first (which are hashable)
    gourmet_domain_tags = [
        Tag(key="cuisine", value="french", author_id="author_1", type="meal"),
        Tag(key="difficulty", value="hard", author_id="author_1", type="meal"),
        Tag(key="occasion", value="special-occasion", author_id="author_1", type="meal"),
        Tag(key="style", value="gourmet", author_id="author_1", type="meal"),
        Tag(key="complexity", value="multi-course", author_id="author_1", type="meal")
    ]
    # Use TagFrozensetAdapter for proper tag frozenset creation
    gourmet_tags = frozenset(ApiTag.from_domain(tag) for tag in gourmet_domain_tags)
    
    scenarios.append({
        "scenario_id": "gourmet_meal_full_nutrition",
        "meal_data": create_api_meal_kwargs(
            name="Five-Course French Tasting Menu",
            description="Elegant five-course French tasting menu featuring classical techniques, seasonal ingredients, and wine pairings. Perfect for special celebrations.",
            recipes=recipes,
            tags=gourmet_tags,
            nutri_facts=nutri_facts,
            weight_in_grams=1000,
            calorie_density=3.2,
            carbo_percentage=60.0,
            protein_percentage=25.0,
            total_fat_percentage=15.0,
        ),
        "max_time_seconds": 0.004,
        "expected_recipe_count": 5,
        "expected_tag_count": 5,
        "description": "Gourmet meal with comprehensive nutrition facts and complex recipe instructions"
    })
    
    return scenarios


# =============================================================================
# CONVERSION TEST DATA FACTORIES
# =============================================================================

def create_domain_meal_for_conversion(recipe_count: int = 3, **kwargs) -> Meal:
    """
    Create a domain Meal for conversion testing.
    
    Args:
        recipe_count: Number of recipes to include
        **kwargs: Override any default values
        
    Returns:
        Domain Meal instance
    """
   
    # Create recipes for the meal first
    recipes = []
    for i in range(recipe_count):
        recipe = create_recipe(
            meal_id=kwargs.get("id", f"meal_{i+1:03d}"),
            author_id=kwargs.get("author_id", f"author_{i+1}")
        )
        recipes.append(recipe)
    
    # Create meal with recipes - use set() for domain entities
    meal_kwargs = create_meal_kwargs(**kwargs)
    meal_kwargs["recipes"] = set(recipes)
    return Meal(**meal_kwargs)


def create_orm_meal_for_conversion(recipe_count: int = 3, **kwargs) -> MealSaModel:
    """
    Create an ORM MealSaModel for conversion testing.
    
    Args:
        recipe_count: Number of recipes to include
        **kwargs: Override any default values
        
    Returns:
        MealSaModel instance
    """
    
    # Create recipes for the meal first
    recipes = []
    for i in range(recipe_count):
        recipe = create_recipe_orm(
            meal_id=kwargs.get("id", f"meal_{i+1:03d}"),
            author_id=kwargs.get("author_id", f"author_{i+1}")
        )
        recipes.append(recipe)
    
    # Create meal with recipes - use list[] for ORM models
    meal_kwargs = create_meal_orm_kwargs(**kwargs)
    meal_kwargs["recipes"] = recipes
    return MealSaModel(**meal_kwargs)


def check_missing_pydantic_fields(pydantic_class: Type[BaseModel], kwargs: Dict[str, Any]) -> list[str]:
    """
    Check for missing required fields in Pydantic model kwargs.
    
    Args:
        pydantic_class: Pydantic model class
        kwargs: Dictionary of field values
        
    Returns:
        List of missing required field names
    """
    if not hasattr(pydantic_class, 'model_fields'):
        return []
    
    required_fields = [
        field_name 
        for field_name, field_info in pydantic_class.model_fields.items()
        if field_info.is_required()
    ]
    
    return [field for field in required_fields if field not in kwargs]


def _get_measure_unit_from_string(unit_string: str) -> MeasureUnit:
    """
    Convert unit string to MeasureUnit enum.
    
    Args:
        unit_string: String representation of the unit
        
    Returns:
        MeasureUnit enum value
    """
    unit_mapping = {
        "g": MeasureUnit.GRAM,
        "ml": MeasureUnit.MILLILITER,
        "cup": MeasureUnit.CUP,
        "cups": MeasureUnit.CUP,
        "tbsp": MeasureUnit.TABLESPOON,
        "tsp": MeasureUnit.TEASPOON,
        "pieces": MeasureUnit.PIECE,
        "piece": MeasureUnit.PIECE,
        "cloves": MeasureUnit.PIECE,
        "l": MeasureUnit.LITER,
        "kg": MeasureUnit.KILOGRAM,
        "slice": MeasureUnit.SLICE,
        "unit": MeasureUnit.UNIT,
        "pinch": MeasureUnit.PINCH,
        "handful": MeasureUnit.HANDFUL
    }
    
    return unit_mapping.get(unit_string.lower(), MeasureUnit.GRAM)  # Default to gram if not found


# Enhanced data factory functions for comprehensive API schema testing
def create_api_rating_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiRating with realistic values."""
    global _RATING_COUNTER
    
    defaults = {
        "user_id": str(uuid.uuid4()),
        "recipe_id": str(uuid.uuid4()),
        "taste": 4,  # 0-5 rating
        "convenience": 3,  # 0-5 rating
        "comment": f"Great recipe! Rating #{_RATING_COUNTER}",
    }
    
    defaults.update(kwargs)
    _RATING_COUNTER += 1
    return defaults


def create_api_rating(**kwargs) -> 'ApiRating':
    """Create ApiRating instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
    
    rating_data = create_api_rating_data(**kwargs)
    return ApiRating(**rating_data)


def create_api_ingredient_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiIngredient with realistic values."""
    global _INGREDIENT_COUNTER
    
    defaults = {
        "name": f"Test Ingredient {_INGREDIENT_COUNTER}",
        "quantity": 1.5,
        "unit": MeasureUnit.GRAM,
        "position": _INGREDIENT_COUNTER,
        "full_text": f"1.5g Test Ingredient {_INGREDIENT_COUNTER}",
        "product_id": str(uuid.uuid4()) if _INGREDIENT_COUNTER % 2 == 0 else None,
    }
    
    defaults.update(kwargs)
    _INGREDIENT_COUNTER += 1
    return defaults


def create_api_ingredient(**kwargs) -> 'ApiIngredient':
    """Create ApiIngredient instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
    
    ingredient_data = create_api_ingredient_data(**kwargs)
    return ApiIngredient(**ingredient_data)


def create_api_user_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiUser with realistic values."""
    global _USER_COUNTER
    
    defaults = {
        "id": str(uuid.uuid4()),
        "roles": set([
            {
                "name": "user",
                "permissions": frozenset(["read", "write"]),
            }
        ]),
    }
    
    defaults.update(kwargs)
    _USER_COUNTER += 1
    return defaults


def create_api_user(**kwargs) -> 'ApiUser':
    """Create ApiUser instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser
    from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api_schemas.role import ApiRole
    
    user_data = create_api_user_data(**kwargs)
    
    # Convert role dicts to ApiRole objects
    if 'roles' in user_data and user_data['roles']:
        api_roles = set()
        for role_data in user_data['roles']:
            if isinstance(role_data, dict):
                api_role = ApiRole(
                    name=role_data["name"],
                    permissions=role_data["permissions"]
                )
                api_roles.add(api_role)
        user_data['roles'] = api_roles
    
    return ApiUser(**user_data)


def create_api_role_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiRole with realistic values."""
    global _ROLE_COUNTER
    
    defaults = {
        "name": f"test_role_{_ROLE_COUNTER}",
        "permissions": frozenset(["read", "write", "delete"]),
    }
    
    defaults.update(kwargs)
    _ROLE_COUNTER += 1
    return defaults


def create_api_role(**kwargs) -> 'ApiRole':
    """Create ApiRole instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api_schemas.role import ApiRole
    
    role_data = create_api_role_data(**kwargs)
    return ApiRole(**role_data)


def create_api_menu_meal_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiMenuMeal with realistic values."""
    global _MENU_MEAL_COUNTER
    
    defaults = {
        "meal_id": str(uuid.uuid4()),
        "position": _MENU_MEAL_COUNTER,
        "meal_type": "breakfast",
        "notes": f"Menu meal notes {_MENU_MEAL_COUNTER}",
    }
    
    defaults.update(kwargs)
    _MENU_MEAL_COUNTER += 1
    return defaults


def create_api_menu_meal(**kwargs) -> 'ApiMenuMeal':
    """Create ApiMenuMeal instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal import ApiMenuMeal
    
    menu_meal_data = create_api_menu_meal_data(**kwargs)
    return ApiMenuMeal(**menu_meal_data)


def create_api_menu_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiMenu with realistic values."""
    global _MENU_COUNTER
    
    defaults = {
        "id": str(uuid.uuid4()),
        "author_id": str(uuid.uuid4()),
        "client_id": str(uuid.uuid4()),
        "name": f"Test Menu {_MENU_COUNTER}",
        "description": f"Test menu description {_MENU_COUNTER}",
        "notes": f"Test menu notes {_MENU_COUNTER}",
        "meals": [],
        "tags": frozenset(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": 1,
    }
    
    defaults.update(kwargs)
    _MENU_COUNTER += 1
    return defaults


def create_api_menu(**kwargs) -> 'ApiMenu':
    """Create ApiMenu instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
    
    menu_data = create_api_menu_data(**kwargs)
    return ApiMenu(**menu_data)


def create_api_client_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiClient with realistic values."""
    global _CLIENT_COUNTER
    
    defaults = {
        "id": str(uuid.uuid4()),
        "author_id": str(uuid.uuid4()),
        "profile": {
            "name": f"Test Client {_CLIENT_COUNTER}",
            "description": f"Test client description {_CLIENT_COUNTER}",
        },
        "contact_info": {
            "email": f"client{_CLIENT_COUNTER}@example.com",
            "phone": f"555-{_CLIENT_COUNTER:04d}",
        },
        "address": {
            "street": f"{_CLIENT_COUNTER} Test Street",
            "city": "Test City",
            "state": "Test State",
            "zip_code": f"{_CLIENT_COUNTER:05d}",
            "country": "Test Country",
        },
        "tags": frozenset(),
        "menus": [],
        "notes": f"Test client notes {_CLIENT_COUNTER}",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": 1,
    }
    
    defaults.update(kwargs)
    _CLIENT_COUNTER += 1
    return defaults


def create_api_client(**kwargs) -> 'ApiClient':
    """Create ApiClient instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import ApiClient
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import ApiContactInfo
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import ApiAddress
    
    client_data = create_api_client_data(**kwargs)
    
    # Convert nested objects to API objects
    if 'profile' in client_data and isinstance(client_data['profile'], dict):
        client_data['profile'] = ApiProfile(**client_data['profile'])
    
    if 'contact_info' in client_data and isinstance(client_data['contact_info'], dict):
        client_data['contact_info'] = ApiContactInfo(**client_data['contact_info'])
    
    if 'address' in client_data and isinstance(client_data['address'], dict):
        client_data['address'] = ApiAddress(**client_data['address'])
    
    return ApiClient(**client_data)


def create_api_create_meal_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiCreateMeal command with realistic values."""
    global _MEAL_COUNTER
    
    defaults = {
        "name": f"Test Meal {_MEAL_COUNTER}",
        "author_id": str(uuid.uuid4()),
        "menu_id": str(uuid.uuid4()),
        "recipes": [],
        "tags": frozenset(),
        "description": f"Test meal description {_MEAL_COUNTER}",
        "notes": f"Test meal notes {_MEAL_COUNTER}",
        "image_url": f"https://example.com/meal{_MEAL_COUNTER}.jpg",
    }
    
    defaults.update(kwargs)
    _MEAL_COUNTER += 1
    return defaults


def create_api_create_meal(**kwargs) -> 'ApiCreateMeal':
    """Create ApiCreateMeal command instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import ApiCreateMeal
    
    create_meal_data = create_api_create_meal_data(**kwargs)
    return ApiCreateMeal(**create_meal_data)


def create_api_update_meal_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiUpdateMeal command with realistic values."""
    global _MEAL_COUNTER
    
    defaults = {
        "id": str(uuid.uuid4()),
        "name": f"Updated Meal {_MEAL_COUNTER}",
        "author_id": str(uuid.uuid4()),
        "recipes": [],
        "tags": frozenset(),
        "description": f"Updated meal description {_MEAL_COUNTER}",
        "notes": f"Updated meal notes {_MEAL_COUNTER}",
        "image_url": f"https://example.com/updated-meal{_MEAL_COUNTER}.jpg",
        "like": True,
        "version": 1,
    }
    
    defaults.update(kwargs)
    _MEAL_COUNTER += 1
    return defaults


def create_api_update_meal(**kwargs) -> 'ApiUpdateMeal':
    """Create ApiUpdateMeal command instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import ApiUpdateMeal
    
    update_meal_data = create_api_update_meal_data(**kwargs)
    return ApiUpdateMeal(**update_meal_data)


def create_api_create_recipe_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiCreateRecipe command with realistic values."""
    global _RECIPE_COUNTER
    
    defaults = {
        "name": f"Test Recipe {_RECIPE_COUNTER}",
        "author_id": str(uuid.uuid4()),
        "meal_id": str(uuid.uuid4()),
        "ingredients": [],
        "tags": frozenset(),
        "description": f"Test recipe description {_RECIPE_COUNTER}",
        "notes": f"Test recipe notes {_RECIPE_COUNTER}",
        "image_url": f"https://example.com/recipe{_RECIPE_COUNTER}.jpg",
        "cooking_time": 30,
        "servings": 4,
        "position": _RECIPE_COUNTER,
    }
    
    defaults.update(kwargs)
    _RECIPE_COUNTER += 1
    return defaults


def create_api_create_recipe(**kwargs) -> 'ApiCreateRecipe':
    """Create ApiCreateRecipe command instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import ApiCreateRecipe
    
    create_recipe_data = create_api_create_recipe_data(**kwargs)
    return ApiCreateRecipe(**create_recipe_data)


def create_api_tag_create_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiCreateTag command with realistic values."""
    global _TAG_COUNTER
    
    defaults = {
        "key": f"test_key_{_TAG_COUNTER}",
        "value": f"test_value_{_TAG_COUNTER}",
        "author_id": str(uuid.uuid4()),
        "type": "recipe",
    }
    
    defaults.update(kwargs)
    _TAG_COUNTER += 1
    return defaults


def create_api_tag_create(**kwargs) -> 'ApiCreateTag':
    """Create ApiCreateTag command instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.commands.tag.create import ApiCreateTag
    
    tag_create_data = create_api_tag_create_data(**kwargs)
    return ApiCreateTag(**tag_create_data)


def create_api_tag_delete_data(**kwargs) -> Dict[str, Any]:
    """Create test data for ApiDeleteTag command with realistic values."""
    global _TAG_COUNTER
    
    defaults = {
        "id": str(uuid.uuid4()),
        "author_id": str(uuid.uuid4()),
    }
    
    defaults.update(kwargs)
    _TAG_COUNTER += 1
    return defaults


def create_api_tag_delete(**kwargs) -> 'ApiDeleteTag':
    """Create ApiDeleteTag command instance with test data."""
    from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.commands.tag.delete import ApiDeleteTag
    
    tag_delete_data = create_api_tag_delete_data(**kwargs)
    return ApiDeleteTag(**tag_delete_data)