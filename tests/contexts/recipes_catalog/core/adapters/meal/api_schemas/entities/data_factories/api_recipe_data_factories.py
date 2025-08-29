"""
Data factories for ApiRecipe testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- JSON serialization/deserialization testing with model_validate_json and model_dump_json
- Parametrized test scenarios for recipe validation
- Performance test scenarios with dataset expectations
- Specialized factory functions for different recipe types
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing
- Complex nested data with ingredients, ratings, tags, and nutrition facts
- Edge case testing for computed properties like average ratings

All data follows the exact structure of ApiRecipe API entities and their validation rules.
Includes extensive testing for Pydantic model validation, JSON handling, and edge cases.
Handles complex round-trip scenarios where computed properties should be corrected.
"""

import json
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, timedelta

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel

# Import check_missing_attributes for validation
from tests.contexts.recipes_catalog.utils import generate_deterministic_id
from tests.utils.utils import check_missing_attributes
from tests.utils.counter_manager import get_next_api_recipe_id

# Import existing data factories for nested objects
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient, create_spice_ingredient, create_vegetable_ingredient, 
    create_meat_ingredient, create_liquid_ingredient, create_baking_ingredient,
)
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_rating_data_factories import (
    create_api_rating, create_excellent_rating, create_mixed_rating,
)


# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_RECIPE_SCENARIOS = [
    {
        "name": "Classic Spaghetti Carbonara",
        "description": "Authentic Italian pasta dish with eggs, cheese, pancetta, and black pepper. A Roman classic that's creamy without cream.",
        "instructions": "1. Cook spaghetti in salted water until al dente. 2. Fry pancetta until crispy. 3. Whisk eggs with cheese. 4. Combine hot pasta with pancetta, remove from heat. 5. Add egg mixture, toss quickly. 6. Season with black pepper and serve immediately.",
        "total_time": 25,
        "privacy": Privacy.PUBLIC,
        "tags": ["cuisine:italian", "difficulty:medium", "meal-type:dinner", "cooking-method:stovetop"],
        "utensils": "Large pot, frying pan, whisk, tongs, cheese grater",
        "notes": "The key is to remove the pan from heat before adding the eggs to prevent scrambling. Use freshly grated Parmigiano-Reggiano for best results.",
        "weight_in_grams": 450,
        "ingredient_count": 6,
        "rating_scenarios": [
            {"taste": 5, "convenience": 3, "comment": "Incredible authentic flavor but requires technique"},
            {"taste": 4, "convenience": 4, "comment": "Delicious and quicker than expected"},
            {"taste": 5, "convenience": 2, "comment": "Perfect taste but tricky timing"}
        ]
    },
    {
        "name": "Quinoa Buddha Bowl",
        "description": "Nutritious bowl with quinoa, roasted vegetables, avocado, and tahini dressing. Perfect for meal prep.",
        "instructions": "1. Cook quinoa according to package instructions. 2. Roast vegetables at 400°F for 25 minutes. 3. Prepare tahini dressing. 4. Assemble bowls with quinoa, vegetables, and toppings. 5. Drizzle with dressing and serve.",
        "total_time": 45,
        "privacy": Privacy.PUBLIC,
        "tags": ["diet:vegetarian", "lifestyle:healthy", "meal-type:lunch", "prep-style:meal-prep"],
        "utensils": "Baking sheet, saucepan, mixing bowls, whisk",
        "notes": "Great for meal prep - stores well in the fridge for 3-4 days. Feel free to substitute vegetables based on seasonal availability.",
        "weight_in_grams": 380,
        "ingredient_count": 10,
        "rating_scenarios": [
            {"taste": 4, "convenience": 5, "comment": "Healthy and very convenient for meal prep"},
            {"taste": 3, "convenience": 4, "comment": "Good for health goals, tasty enough"},
            {"taste": 5, "convenience": 5, "comment": "Perfect balance of nutrition and flavor"}
        ]
    },
    {
        "name": "Slow-Cooked Beef Stew",
        "description": "Hearty comfort food with tender beef, vegetables, and rich gravy. Perfect for cold days.",
        "instructions": "1. Brown beef in batches. 2. Sauté onions and garlic. 3. Add tomato paste, cook 1 minute. 4. Add wine, scraping up browned bits. 5. Add beef, broth, and herbs. 6. Simmer 2-3 hours until tender. 7. Add vegetables in last 30 minutes.",
        "total_time": 180,
        "privacy": Privacy.PUBLIC,
        "tags": ["mood:comfort-food", "cooking-method:slow-cook", "meal-type:dinner", "season:winter"],
        "utensils": "Dutch oven, wooden spoon, ladle, cutting board, sharp knife",
        "notes": "This stew tastes even better the next day. Can be made in a slow cooker on low for 6-8 hours. Serve with crusty bread.",
        "weight_in_grams": 600,
        "ingredient_count": 12,
        "rating_scenarios": [
            {"taste": 5, "convenience": 2, "comment": "Amazing comfort food but takes all day"},
            {"taste": 4, "convenience": 3, "comment": "Worth the time investment for flavor"},
            {"taste": 5, "convenience": 4, "comment": "Perfect for slow cooker - set and forget"}
        ]
    },
    {
        "name": "Thai Green Curry",
        "description": "Aromatic and spicy curry with coconut milk, vegetables, and fresh herbs. Authentic Thai flavors.",
        "instructions": "1. Heat oil in wok. 2. Fry curry paste until fragrant. 3. Add coconut milk gradually. 4. Add protein and hard vegetables. 5. Simmer 10 minutes. 6. Add soft vegetables and seasonings. 7. Garnish with herbs and serve with rice.",
        "total_time": 35,
        "privacy": Privacy.PUBLIC,
        "tags": ["cuisine:thai", "dietary:spicy", "meal-type:dinner", "cooking-method:stovetop"],
        "utensils": "Wok or large pan, wooden spoon, knife, cutting board",
        "notes": "Adjust spice level by using more or less curry paste. Fish sauce is essential for authentic flavor. Serve with jasmine rice.",
        "weight_in_grams": 420,
        "ingredient_count": 14,
        "rating_scenarios": [
            {"taste": 5, "convenience": 4, "comment": "Authentic Thai flavors, surprisingly easy"},
            {"taste": 4, "convenience": 3, "comment": "Great taste but hard to find some ingredients"},
            {"taste": 5, "convenience": 5, "comment": "Quick, delicious, and satisfying"}
        ]
    },
    {
        "name": "Chocolate Lava Cake",
        "description": "Decadent individual chocolate cakes with molten centers. Perfect for special occasions.",
        "instructions": "1. Preheat oven to 425°F. 2. Melt chocolate and butter. 3. Whisk in eggs and sugar. 4. Fold in flour. 5. Pour into greased ramekins. 6. Bake 12-14 minutes until edges are firm. 7. Invert onto plates and serve immediately.",
        "total_time": 30,
        "privacy": Privacy.PUBLIC,
        "tags": ["meal-type:dessert", "occasion:special-occasion", "difficulty:medium", "mood:indulgent"],
        "utensils": "Ramekins, double boiler, whisk, mixing bowls, sieve",
        "notes": "Timing is crucial - overcooking will set the center. Can be prepared ahead and baked just before serving. Serve with vanilla ice cream.",
        "weight_in_grams": 200,
        "ingredient_count": 6,
        "rating_scenarios": [
            {"taste": 5, "convenience": 2, "comment": "Absolutely delicious but timing is tricky"},
            {"taste": 5, "convenience": 3, "comment": "Worth the effort for special occasions"},
            {"taste": 4, "convenience": 4, "comment": "Easier than expected and very impressive"}
        ]
    }
]

COMMON_RECIPE_TYPES = [
    "appetizer", "soup", "salad", "main_course", "side_dish", "dessert", 
    "breakfast", "lunch", "dinner", "snack", "beverage", "sauce"
]

CUISINE_TYPES = [
    "italian", "asian", "mexican", "mediterranean", "american", "french", 
    "indian", "thai", "chinese", "japanese", "greek", "middle_eastern"
]

DIETARY_TAGS = [
    "vegetarian", "vegan", "gluten-free", "dairy-free", "keto", "paleo", 
    "low-carb", "high-protein", "healthy", "spicy", "mild"
]

DIFFICULTY_LEVELS = ["easy", "medium", "hard", "expert"]

COOKING_METHODS = [
    "stovetop", "oven", "grill", "slow-cook", "pressure-cook", "no-cook", 
    "air-fry", "steam", "saute", "bake", "roast", "broil"
]

# =============================================================================
# HELPER FUNCTIONS FOR NESTED OBJECTS
# =============================================================================

def create_api_recipe_tag(**kwargs) -> ApiTag:
    """Create an ApiTag for testing with realistic data"""
    # Create realistic tag combinations
    tag_combinations = [
        {"key": "cuisine", "value": "italian"},
        {"key": "difficulty", "value": "medium"},
        {"key": "meal-type", "value": "dinner"},
        {"key": "diet", "value": "vegetarian"},
        {"key": "cooking-method", "value": "stovetop"},
        {"key": "occasion", "value": "weeknight"},
        {"key": "season", "value": "summer"},
        {"key": "lifestyle", "value": "healthy"},
        {"key": "mood", "value": "comfort-food"},
        {"key": "prep-style", "value": "meal-prep"}
    ]
    
    recipe_counter = get_next_api_recipe_id()
    tag_index = (recipe_counter - 1) % len(tag_combinations)
    tag_data = tag_combinations[tag_index]
    post_fix = kwargs.get("post_fix", "")
    
    final_kwargs = {
        "key": kwargs.get("key", tag_data["key"]),
        "value": kwargs.get("value", tag_data["value"]+post_fix),
        "author_id": kwargs.get("author_id", str(uuid4())),
        "type": kwargs.get("type", "recipe"),
        **{k: v for k, v in kwargs.items() if k not in ["key", "value", "author_id", "type", "post_fix"]}
    }
    
    return ApiTag(**final_kwargs)


def create_api_nutri_facts(**kwargs) -> ApiNutriFacts:
    """Create realistic ApiNutriFacts for testing"""
    # Create realistic nutrition profiles based on recipe type
    nutrition_profiles = [
        # Pasta dish
        {"calories": 520.0, "protein": 22.0, "carbohydrate": 65.0, "total_fat": 18.0, "sodium": 890.0},
        # Healthy bowl
        {"calories": 380.0, "protein": 15.0, "carbohydrate": 45.0, "total_fat": 12.0, "sodium": 420.0},
        # Hearty stew
        {"calories": 420.0, "protein": 32.0, "carbohydrate": 28.0, "total_fat": 16.0, "sodium": 1200.0},
        # Curry
        {"calories": 460.0, "protein": 18.0, "carbohydrate": 35.0, "total_fat": 28.0, "sodium": 950.0},
        # Dessert
        {"calories": 650.0, "protein": 8.0, "carbohydrate": 72.0, "total_fat": 38.0, "sodium": 180.0}
    ]
    
    recipe_counter = get_next_api_recipe_id()
    profile_index = (recipe_counter - 1) % len(nutrition_profiles)
    profile = nutrition_profiles[profile_index]
    
    final_kwargs = {
        "calories": kwargs.get("calories", profile["calories"]),
        "protein": kwargs.get("protein", profile["protein"]),
        "carbohydrate": kwargs.get("carbohydrate", profile["carbohydrate"]),
        "total_fat": kwargs.get("total_fat", profile["total_fat"]),
        "saturated_fat": kwargs.get("saturated_fat", profile["total_fat"] * 0.3),
        "trans_fat": kwargs.get("trans_fat", 0.1),
        "sugar": kwargs.get("sugar", profile["carbohydrate"] * 0.15),
        "sodium": kwargs.get("sodium", profile["sodium"]),
        "dietary_fiber": kwargs.get("dietary_fiber", 5.0 + (recipe_counter % 10)),
        **{k: v for k, v in kwargs.items() if k not in ["calories", "protein", "carbohydrate", "total_fat", "saturated_fat", "trans_fat", "sugar", "sodium", "dietary_fiber"]}
    }
    
    return ApiNutriFacts(**final_kwargs)


# =============================================================================
# API RECIPE DATA FACTORIES
# =============================================================================

def create_api_recipe_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ApiRecipe kwargs with deterministic values and comprehensive validation.
    
    Uses check_missing_attributes to ensure completeness and generates
    realistic test data for comprehensive API testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ApiRecipe creation parameters
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Get realistic recipe scenario for deterministic values
    recipe_counter = get_next_api_recipe_id()
    scenario = REALISTIC_RECIPE_SCENARIOS[(recipe_counter - 1) % len(REALISTIC_RECIPE_SCENARIOS)]
    
    # Check if ingredients are provided in kwargs first, otherwise create default ones
    if "ingredients" in kwargs:
        ingredients = kwargs["ingredients"]
    else:
        # Create ingredients based on scenario - now as frozenset
        ingredients = []
        for i in range(scenario["ingredient_count"]):
            ingredient = create_api_ingredient(position=i)
            ingredients.append(ingredient)
        ingredients = frozenset(ingredients)

    # Check if ratings are provided in kwargs first, otherwise create default ones
    if "ratings" in kwargs:
        ratings = kwargs["ratings"]
    else:
        # Create ratings based on scenario - now as frozenset
        ratings = []
        for rating_scenario in scenario["rating_scenarios"]:
            rating = create_api_rating(
                taste=rating_scenario["taste"],
                convenience=rating_scenario["convenience"],
                comment=rating_scenario["comment"]
            )
            ratings.append(rating)
        ratings = frozenset(ratings)

    # Check if tags are provided in kwargs first, otherwise create default ones
    if "tags" in kwargs:
        tags = kwargs["tags"]
    else:
        # Create tags from scenario
        tags = []
        for tag_string in scenario["tags"]:
            if isinstance(tag_string, ApiTag):
                tags.append(tag_string)
                continue
            if ":" in tag_string:
                key, value = tag_string.split(":", 1)
                tag = create_api_recipe_tag(key=key, value=value, author_id=recipe_author_id)
                tags.append(tag)
            else:
                tag = create_api_recipe_tag(key="general", value=tag_string, author_id=recipe_author_id)
                tags.append(tag)
        tags = frozenset(tags)
    
    # Calculate realistic average ratings from the actual ratings that will be used
    if ratings:
        avg_taste = sum(r.taste for r in ratings) / len(ratings)
        avg_convenience = sum(r.convenience for r in ratings) / len(ratings)
    else:
        avg_taste = None
        avg_convenience = None
    
    # Create base timestamp
    base_time = datetime.now() - timedelta(days=recipe_counter)
    
    final_kwargs = {
        "id": kwargs.get("id", str(uuid4())),
        "name": kwargs.get("name", scenario["name"]),
        "description": kwargs.get("description", scenario["description"]),
        "instructions": kwargs.get("instructions", scenario["instructions"]),
        "author_id": recipe_author_id,
        "meal_id": kwargs.get("meal_id", str(uuid4())),
        "ingredients": ingredients,  # Use the resolved ingredients (from kwargs or defaults)
        "utensils": kwargs.get("utensils", scenario["utensils"]),
        "total_time": kwargs.get("total_time", scenario["total_time"]),
        "notes": kwargs.get("notes", scenario["notes"]),
        "tags": tags,  # Use the resolved tags (from kwargs or defaults)
        "privacy": kwargs.get("privacy", scenario["privacy"]),
        "ratings": ratings,  # Use the resolved ratings (from kwargs or defaults)
        "nutri_facts": kwargs.get("nutri_facts", create_api_nutri_facts()),
        "weight_in_grams": kwargs.get("weight_in_grams", scenario["weight_in_grams"]),
        "image_url": kwargs.get("image_url", f"https://example.com/recipe_{recipe_counter}.jpg" if recipe_counter % 2 == 0 else None),
        "average_taste_rating": kwargs.get("average_taste_rating", avg_taste),
        "average_convenience_rating": kwargs.get("average_convenience_rating", avg_convenience),
        "created_at": kwargs.get("created_at", base_time),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Allow override of any other attributes except author_id (to maintain consistency with tags)
    for key, value in kwargs.items():
        if key not in final_kwargs and key != "author_id":
            final_kwargs[key] = value
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiRecipe, final_kwargs)
    missing = set(missing) - {'convert', 'model_computed_fields', 'model_config', 'model_fields'}
    assert not missing, f"Missing attributes for ApiRecipe: {missing}"
    
    return final_kwargs


def create_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create an ApiRecipe instance with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe instance with comprehensive validation
    """
    recipe_kwargs = create_api_recipe_kwargs(**kwargs)
    return ApiRecipe(**recipe_kwargs)


def create_api_recipe_from_json(json_data: Optional[str] = None, **kwargs) -> ApiRecipe:
    """
    Create an ApiRecipe instance from JSON using model_validate_json.
    
    This tests Pydantic's JSON validation and parsing capabilities.
    
    Args:
        json_data: JSON string to parse (if None, generates from kwargs)
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe instance created from JSON
    """
    if json_data is None:
        recipe_kwargs = create_api_recipe_kwargs(**kwargs)
        # Convert complex objects to JSON-serializable format
        recipe_kwargs = _convert_to_json_serializable(recipe_kwargs)
        json_data = json.dumps(recipe_kwargs)
    
    return ApiRecipe.model_validate_json(json_data)


def create_api_recipe_json(**kwargs) -> str:
    """
    Create JSON representation of ApiRecipe using model_dump_json.
    
    This tests Pydantic's JSON serialization capabilities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        JSON string representation of ApiRecipe
    """
    recipe = create_api_recipe(**kwargs)
    return recipe.model_dump_json()


def _convert_to_json_serializable(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert complex objects to JSON-serializable format"""
    converted = {}
    
    for key, value in data.items():
        if isinstance(value, frozenset):
            if key == "ingredients":
                # Convert frozenset of ingredients to list of dicts = ingredient.unit.value
                converted[key] = [
                    {
                        "name": ingredient.name,
                        "quantity": ingredient.quantity,
                        "unit": ingredient.unit.value if isinstance(ingredient.unit, MeasureUnit) else ingredient.unit,
                        "position": ingredient.position,
                        "full_text": ingredient.full_text,
                        "product_id": ingredient.product_id
                    }
                    for ingredient in value
                ]
            elif key == "ratings":
                # Convert frozenset of ratings to list of dicts
                converted[key] = [
                    {
                        "user_id": rating.user_id,
                        "recipe_id": rating.recipe_id,
                        "taste": rating.taste,
                        "convenience": rating.convenience,
                        "comment": rating.comment
                    }
                    for rating in value
                ]
            elif key == "tags":
                # Convert frozenset of tags to list of dicts
                converted[key] = [
                    {"key": tag.key, "value": tag.value, "author_id": tag.author_id, "type": tag.type}
                    for tag in value
                ]
            else:
                # Generic frozenset conversion
                converted[key] = list(value)
        elif isinstance(value, list) and value:
            # Convert list of potential Pydantic objects to list of dicts
            converted_items = []
            for item in value:
                try:
                    converted_items.append(item.model_dump())
                except AttributeError:
                    converted_items.append(item)
            converted[key] = converted_items
        elif hasattr(value, 'model_dump'):
            # Convert Pydantic object to dict
            converted[key] = value.model_dump() # type: ignore
        elif isinstance(value, datetime):
            # Convert datetime to ISO string
            converted[key] = value.isoformat()
        elif isinstance(value, Privacy):
            # Convert enum to string
            converted[key] = value.value
        else:
            converted[key] = value
    
    return converted


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_simple_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a simple recipe with minimal ingredients and basic preparation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with simple preparation
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))

    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Simple Toast"),
        "description": kwargs.get("description", "Quick and easy toast with butter"),
        "instructions": kwargs.get("instructions", "1. Toast bread. 2. Spread butter. 3. Serve."),
        "total_time": kwargs.get("total_time", 5),
        "ingredients": kwargs.get("ingredients", frozenset([
            create_api_ingredient(name="Bread", quantity=2.0, unit=MeasureUnit.SLICE, position=0),
            create_api_ingredient(name="Butter", quantity=1.0, unit=MeasureUnit.TABLESPOON, position=1)
        ])),
        "tags": kwargs.get("tags", frozenset([
            create_api_recipe_tag(key="difficulty", value="easy", author_id=recipe_author_id),
            create_api_recipe_tag(key="meal-type", value="breakfast", author_id=recipe_author_id)
        ])),
        "ratings": kwargs.get("ratings", frozenset([
            create_api_rating(taste=3, convenience=5, comment="Simple but effective")
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "total_time", "ingredients", "tags", "ratings", "author_id"]}
    }
    return create_api_recipe(**final_kwargs)


def create_complex_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a complex recipe with many ingredients and detailed preparation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with complex preparation
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Create complex ingredients list - now as frozenset
    complex_ingredients = frozenset([
        create_meat_ingredient(name="Beef Tenderloin", quantity=800.0, position=0),
        create_vegetable_ingredient(name="Shallots", quantity=3.0, position=1),
        create_liquid_ingredient(name="Red Wine", quantity=250.0, position=2),
        create_liquid_ingredient(name="Beef Stock", quantity=500.0, position=3),
        create_spice_ingredient(name="Thyme", quantity=1.0, position=4),
        create_spice_ingredient(name="Bay Leaves", quantity=2.0, position=5),
        create_baking_ingredient(name="Flour", quantity=2.0, position=6),
        create_api_ingredient(name="Mushrooms", quantity=300.0, unit=MeasureUnit.GRAM, position=7),
        create_api_ingredient(name="Heavy Cream", quantity=200.0, unit=MeasureUnit.MILLILITER, position=8),
        create_api_ingredient(name="Butter", quantity=100.0, unit=MeasureUnit.GRAM, position=9)
    ])
    
    # Create multiple detailed ratings - now as frozenset
    complex_ratings = frozenset([
        create_excellent_rating(comment="Restaurant-quality dish! Worth every minute of preparation."),
        create_mixed_rating(comment="Amazing flavors but very time-consuming and requires skill."),
        create_api_rating(taste=4, convenience=2, comment="Impressive results but not for beginners.")
    ])

    complex_tags = frozenset([
        create_api_recipe_tag(key="cuisine", value="french", author_id=recipe_author_id),
        create_api_recipe_tag(key="difficulty", value="expert", author_id=recipe_author_id),
        create_api_recipe_tag(key="occasion", value="special-occasion", author_id=recipe_author_id),
        create_api_recipe_tag(key="cooking-method", value="oven", author_id=recipe_author_id),
        create_api_recipe_tag(key="mood", value="impressive", author_id=recipe_author_id)
    ])
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Beef Wellington with Mushroom Duxelles"),
        "description": kwargs.get("description", "Classic French dish featuring beef tenderloin wrapped in puff pastry with mushroom duxelles and pâté. A true test of culinary skill."),
        "instructions": kwargs.get("instructions", "1. Sear beef tenderloin on all sides. 2. Prepare mushroom duxelles by sautéing mushrooms until moisture evaporates. 3. Wrap beef in plastic with duxelles, chill 30 minutes. 4. Roll out puff pastry. 5. Wrap beef in pastry, seal edges. 6. Egg wash and score. 7. Bake at 400°F for 25-30 minutes. 8. Rest 10 minutes before slicing."),
        "total_time": kwargs.get("total_time", 120),
        "ingredients": kwargs.get("ingredients", complex_ingredients),
        "tags": kwargs.get("tags", complex_tags),
        "ratings": kwargs.get("ratings", complex_ratings),
        "utensils": kwargs.get("utensils", "Large skillet, baking sheet, rolling pin, pastry brush, meat thermometer, sharp knife, cutting board"),
        "notes": kwargs.get("notes", "This is an advanced recipe requiring precise timing and technique. Use a meat thermometer for perfect doneness. Allow beef to rest before wrapping to prevent pastry from becoming soggy."),
        "weight_in_grams": kwargs.get("weight_in_grams", 1200),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "total_time", "ingredients", "tags", "ratings", "utensils", "notes", "weight_in_grams"]}
    }
    return create_api_recipe(**final_kwargs)


def create_vegetarian_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a vegetarian recipe with plant-based ingredients.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with vegetarian ingredients
    """
    author_id = kwargs.get("author_id", str(uuid4()))

    vegetarian_ingredients = frozenset([
        create_vegetable_ingredient(name="Eggplant", quantity=2.0, position=0),
        create_vegetable_ingredient(name="Zucchini", quantity=1.0, position=1),
        create_vegetable_ingredient(name="Bell Peppers", quantity=2.0, position=2),
        create_api_ingredient(name="Tomatoes", quantity=400.0, unit=MeasureUnit.GRAM, position=3),
        create_api_ingredient(name="Mozzarella", quantity=200.0, unit=MeasureUnit.GRAM, position=4),
        create_spice_ingredient(name="Oregano", quantity=1.0, position=5),
        create_spice_ingredient(name="Basil", quantity=2.0, position=6),
        create_api_ingredient(name="Olive Oil", quantity=3.0, unit=MeasureUnit.TABLESPOON, position=7)
    ])
    
    final_kwargs = {
        "author_id": author_id,
        "name": kwargs.get("name", "Mediterranean Vegetable Gratin"),
        "description": kwargs.get("description", "Layered vegetable gratin with Mediterranean flavors, perfect for vegetarians."),
        "instructions": kwargs.get("instructions", "1. Slice vegetables thinly. 2. Layer in baking dish with cheese and herbs. 3. Drizzle with olive oil. 4. Bake at 375°F for 45 minutes until golden."),
        "total_time": kwargs.get("total_time", 60),
        "ingredients": kwargs.get("ingredients", vegetarian_ingredients),
        "tags": kwargs.get("tags", frozenset([
            create_api_recipe_tag(key="diet", value="vegetarian", author_id=author_id),
            create_api_recipe_tag(key="cuisine", value="mediterranean", author_id=author_id),
            create_api_recipe_tag(key="cooking-method", value="oven", author_id=author_id),
            create_api_recipe_tag(key="meal-type", value="dinner", author_id=author_id)
        ])),
        "nutri_facts": kwargs.get("nutri_facts", create_api_nutri_facts(
            calories=320.0, protein=18.0, carbohydrate=25.0, total_fat=15.0
        )),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "total_time", "ingredients", "tags", "nutri_facts"]}
    }
    return create_api_recipe(**final_kwargs)


def create_high_protein_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a high-protein recipe optimized for fitness goals.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with high protein content
    """
    # Get the recipe's author_id early so we can use it for tags
    author_id = kwargs.get("author_id", str(uuid4()))
    
    high_protein_ingredients = frozenset([
        create_meat_ingredient(name="Chicken Breast", quantity=200.0, position=0),
        create_api_ingredient(name="Greek Yogurt", quantity=150.0, unit=MeasureUnit.GRAM, position=1),
        create_api_ingredient(name="Eggs", quantity=2.0, unit=MeasureUnit.UNIT, position=2),
        create_api_ingredient(name="Quinoa", quantity=100.0, unit=MeasureUnit.GRAM, position=3),
        create_api_ingredient(name="Almonds", quantity=30.0, unit=MeasureUnit.GRAM, position=4),
        create_vegetable_ingredient(name="Spinach", quantity=100.0, position=5)
    ])
    
    final_kwargs = {
        "author_id": author_id,
        "name": kwargs.get("name", "High-Protein Power Bowl"),
        "description": kwargs.get("description", "Nutrient-dense bowl packed with high-quality protein sources for muscle building and recovery."),
        "total_time": kwargs.get("total_time", 25),
        "ingredients": kwargs.get("ingredients", high_protein_ingredients),
        "tags": kwargs.get("tags", frozenset([
            create_api_recipe_tag(key="lifestyle", value="fitness", author_id=author_id),
            create_api_recipe_tag(key="diet", value="high-protein", author_id=author_id),
            create_api_recipe_tag(key="meal-type", value="lunch", author_id=author_id),
            create_api_recipe_tag(key="prep-style", value="meal-prep", author_id=author_id)
        ])),
        "nutri_facts": kwargs.get("nutri_facts", create_api_nutri_facts(
            calories=520.0, protein=45.0, carbohydrate=35.0, total_fat=18.0
        )),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "total_time", "ingredients", "tags", "nutri_facts", "author_id"]}
    }
    return create_api_recipe(**final_kwargs)


def create_quick_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a quick recipe that can be made in 15 minutes or less.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with quick preparation
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    
    final_kwargs = {
        "author_id": author_id,
        "name": kwargs.get("name", "15-Minute Stir Fry"),
        "description": kwargs.get("description", "Quick and healthy stir fry perfect for busy weeknights."),
        "instructions": kwargs.get("instructions", "1. Heat oil in wok. 2. Add vegetables, stir-fry 3 minutes. 3. Add sauce, cook 2 minutes. 4. Serve over rice."),
        "total_time": kwargs.get("total_time", 15),
        "tags": kwargs.get("tags", frozenset([
            create_api_recipe_tag(key="speed", value="quick", author_id=author_id),
            create_api_recipe_tag(key="difficulty", value="easy", author_id=author_id),
            create_api_recipe_tag(key="cooking-method", value="stir-fry", author_id=author_id),
            create_api_recipe_tag(key="occasion", value="weeknight", author_id=author_id)
        ])),
        "ratings": kwargs.get("ratings", frozenset([
            create_api_rating(taste=4, convenience=5, comment="Perfect for busy nights!")
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "total_time", "tags", "ratings"]}
    }
    return create_api_recipe(**final_kwargs)


def create_dessert_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a dessert recipe with sweet ingredients.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe for dessert
    """
    author_id = kwargs.get("author_id", str(uuid4()))

    dessert_ingredients = frozenset([
        create_baking_ingredient(name="All-Purpose Flour", quantity=2.0, position=0),
        create_api_ingredient(name="Sugar", quantity=150.0, unit=MeasureUnit.GRAM, position=1),
        create_api_ingredient(name="Dark Chocolate", quantity=200.0, unit=MeasureUnit.GRAM, position=2),
        create_api_ingredient(name="Butter", quantity=100.0, unit=MeasureUnit.GRAM, position=3),
        create_api_ingredient(name="Eggs", quantity=3.0, unit=MeasureUnit.UNIT, position=4),
        create_api_ingredient(name="Vanilla Extract", quantity=1.0, unit=MeasureUnit.TEASPOON, position=5)
    ])
    
    final_kwargs = {
        "author_id": author_id,
        "name": kwargs.get("name", "Decadent Chocolate Brownies"),
        "description": kwargs.get("description", "Rich, fudgy brownies with intense chocolate flavor."),
        "ingredients": kwargs.get("ingredients", dessert_ingredients),
        "tags": kwargs.get("tags", frozenset([
            create_api_recipe_tag(key="meal-type", value="dessert", author_id=author_id),
            create_api_recipe_tag(key="mood", value="indulgent", author_id=author_id),
            create_api_recipe_tag(key="cooking-method", value="bake", author_id=author_id),
            create_api_recipe_tag(key="occasion", value="treat", author_id=author_id)
        ])),
        "nutri_facts": kwargs.get("nutri_facts", create_api_nutri_facts(
            calories=380.0, protein=5.0, carbohydrate=45.0, total_fat=22.0, sugar=35.0
        )),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "ingredients", "tags", "nutri_facts"]}
    }
    return create_api_recipe(**final_kwargs)


def create_api_recipe_with_incorrect_averages(**kwargs) -> ApiRecipe:
    """
    Create a recipe with deliberately incorrect average ratings for testing round-trip corrections.
    
    This tests the edge case where JSON contains average ratings that don't match the computed values.
    When converted to domain and back, the averages should be corrected.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with incorrect average ratings
    """
    # Check if ratings are provided in kwargs first, otherwise create default ones
    if "ratings" in kwargs:
        ratings = kwargs["ratings"]
    else:
        # Create specific ratings that give known averages - now as frozenset
        ratings = frozenset([
            create_api_rating(taste=4, convenience=2, comment="Great taste, takes time"),
            create_api_rating(taste=5, convenience=3, comment="Excellent flavor, moderate effort"),
            create_api_rating(taste=3, convenience=4, comment="Good and convenient")
        ])
    
    # Calculate what the TRUE averages should be from the actual ratings that will be used
    if ratings:
        true_taste_avg = sum(r.taste for r in ratings) / len(ratings)
        true_convenience_avg = sum(r.convenience for r in ratings) / len(ratings)
        
        # Create deliberately incorrect averages (offset by -1.5 from true values)
        incorrect_taste_avg = max(1.0, true_taste_avg - 1.5)  # Ensure it stays within valid range
        incorrect_convenience_avg = max(1.0, true_convenience_avg - 2.0)  # Ensure it stays within valid range
    else:
        # If no ratings, use None for averages
        incorrect_taste_avg = None
        incorrect_convenience_avg = None
    
    final_kwargs = {
        "name": kwargs.get("name", "Recipe with Incorrect Averages"),
        "ratings": ratings,  # Use the resolved ratings (from kwargs or defaults)
        "average_taste_rating": kwargs.get("average_taste_rating", incorrect_taste_avg),
        "average_convenience_rating": kwargs.get("average_convenience_rating", incorrect_convenience_avg),
        **{k: v for k, v in kwargs.items() if k not in ["name", "ratings", "average_taste_rating", "average_convenience_rating"]}
    }
    return create_api_recipe(**final_kwargs)


def create_api_recipe_without_ratings(**kwargs) -> ApiRecipe:
    """
    Create a recipe without any ratings for testing null average handling.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with no ratings
    """
    final_kwargs = {
        "name": kwargs.get("name", "Unrated Recipe"),
        "ratings": kwargs.get("ratings", frozenset()),
        "average_taste_rating": kwargs.get("average_taste_rating", None),
        "average_convenience_rating": kwargs.get("average_convenience_rating", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "ratings", "average_taste_rating", "average_convenience_rating"]}
    }
    return create_api_recipe(**final_kwargs)


def create_api_recipe_with_max_fields(**kwargs) -> ApiRecipe:
    """
    Create a recipe with maximum field lengths for testing limits.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with maximum field lengths
    """
    # Get the recipe's author_id early so we can use it for tags
    author_id = kwargs.get("author_id", str(uuid4()))
    
    # Create maximum length strings based on actual validation constraints
    max_name = "A" * 500  # RecipeNameRequired has max_length=500
    max_description = "B" * 1000  # RecipeDescriptionOptional validator limit is 1000
    max_instructions = "C" * 15000  # RecipeInstructionsRequired has max_length=15000
    max_notes = "D" * 1000  # RecipeNotesOptional validator limit is 1000
    max_utensils = "E" * 500  # RecipeUtensilsOptional validator limit is 500
    
    # Create many ingredients and ratings - now as frozensets
    max_ingredients = frozenset([create_api_ingredient(position=i) for i in range(50)])  # Assuming max 50 ingredients
    max_ratings = frozenset([create_api_rating() for _ in range(100)])  # Assuming max 100 ratings
    max_tags = frozenset([create_api_recipe_tag(author_id=author_id, post_fix=str(i)) for i in range(20)])  # Assuming max 20 tags
    
    final_kwargs = {
        "author_id": author_id,
        "name": kwargs.get("name", max_name),
        "description": kwargs.get("description", max_description),
        "instructions": kwargs.get("instructions", max_instructions),
        "notes": kwargs.get("notes", max_notes),
        "utensils": kwargs.get("utensils", max_utensils),
        "ingredients": kwargs.get("ingredients", max_ingredients),
        "ratings": kwargs.get("ratings", max_ratings),
        "tags": kwargs.get("tags", max_tags),
        "total_time": kwargs.get("total_time", 999),  # Max reasonable time
        "weight_in_grams": kwargs.get("weight_in_grams", 10000),  # Max reasonable weight
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "notes", "utensils", "ingredients", "ratings", "tags", "total_time", "weight_in_grams", "author_id"]}
    }
    return create_api_recipe(**final_kwargs)


def create_minimal_api_recipe(**kwargs) -> ApiRecipe:
    """
    Create a recipe with only required fields for testing minimums.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRecipe with minimal required fields
    """
    final_kwargs = {
        "name": kwargs.get("name", "Minimal Recipe"),
        "instructions": kwargs.get("instructions", "Cook it."),
        "author_id": kwargs.get("author_id", str(uuid4())),
        "meal_id": kwargs.get("meal_id", str(uuid4())),
        "ingredients": kwargs.get("ingredients", frozenset()),
        "description": kwargs.get("description", None),
        "utensils": kwargs.get("utensils", None),
        "total_time": kwargs.get("total_time", None),
        "notes": kwargs.get("notes", None),
        "tags": kwargs.get("tags", frozenset()),
        "privacy": kwargs.get("privacy", Privacy.PRIVATE),
        "ratings": kwargs.get("ratings", frozenset()),
        "nutri_facts": kwargs.get("nutri_facts", None),
        "weight_in_grams": kwargs.get("weight_in_grams", None),
        "image_url": kwargs.get("image_url", None),
        "average_taste_rating": kwargs.get("average_taste_rating", None),
        "average_convenience_rating": kwargs.get("average_convenience_rating", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "instructions", "author_id", "meal_id", "ingredients", "description", "utensils", "total_time", "notes", "tags", "privacy", "ratings", "nutri_facts", "weight_in_grams", "image_url", "average_taste_rating", "average_convenience_rating"]}
    }
    return create_api_recipe(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_recipe_collection(count: int = 10) -> List[ApiRecipe]:
    """Create a collection of diverse recipes for testing"""
    recipes = []
    
    for i in range(count):
        if i % 5 == 0:
            recipe = create_simple_api_recipe()
        elif i % 5 == 1:
            recipe = create_complex_api_recipe()
        elif i % 5 == 2:
            recipe = create_vegetarian_api_recipe()
        elif i % 5 == 3:
            recipe = create_quick_api_recipe()
        else:
            recipe = create_dessert_api_recipe()
        
        recipes.append(recipe)
    
    return recipes


def create_api_recipes_by_cuisine(cuisine: str, count: int = 5) -> List[ApiRecipe]:
    """Create multiple recipes for a specific cuisine"""
    recipes = []
    
    for i in range(count):
        # Get the recipe's author_id early so we can use it for tags
        author_id = str(uuid4())
        
        recipe = create_api_recipe(
            name=f"{cuisine.title()} Recipe {i+1}",
            author_id=author_id,
            tags=frozenset([create_api_recipe_tag(key="cuisine", value=cuisine, author_id=author_id)])
        )
        recipes.append(recipe)
    
    return recipes


def create_api_recipes_by_difficulty(difficulty: str, count: int = 5) -> List[ApiRecipe]:
    """Create multiple recipes for a specific difficulty level"""
    recipes = []
    
    for i in range(count):
        # Get the recipe's author_id early so we can use it for tags
        author_id = str(uuid4())
        
        if difficulty == "easy":
            recipe = create_simple_api_recipe(author_id=author_id)
        elif difficulty == "hard":
            recipe = create_complex_api_recipe(author_id=author_id)
        else:
            recipe = create_api_recipe(
                author_id=author_id,
                tags=frozenset([create_api_recipe_tag(key="difficulty", value=difficulty, author_id=author_id)])
            )
        
        recipes.append(recipe)
    
    return recipes


def create_test_dataset_for_api_recipe(count: int = 100) -> Dict[str, Any]:
    """Create a dataset of recipes for performance testing"""
    recipes = []
    json_strings = []
    
    for i in range(count):
        # Create API recipe
        recipe_kwargs = create_api_recipe_kwargs()
        recipe = create_api_recipe(**recipe_kwargs)
        recipes.append(recipe)
        
        # Create JSON representation
        json_string = recipe.model_dump_json()
        json_strings.append(json_string)
    
    return {
        "recipes": recipes,
        "json_strings": json_strings,
        "total_recipes": len(recipes)
    }


# =============================================================================
# DOMAIN AND ORM CONVERSION HELPERS
# =============================================================================

def create_recipe_domain_from_api(api_recipe: ApiRecipe) -> _Recipe:
    """Convert ApiRecipe to domain Recipe using to_domain method"""
    return api_recipe.to_domain()


def create_api_recipe_from_domain(domain_recipe: _Recipe) -> ApiRecipe:
    """Convert domain Recipe to ApiRecipe using from_domain method"""
    return ApiRecipe.from_domain(domain_recipe)


def create_recipe_orm_kwargs_from_api(api_recipe: ApiRecipe) -> Dict[str, Any]:
    """Convert ApiRecipe to ORM kwargs using to_orm_kwargs method"""
    return api_recipe.to_orm_kwargs()


def create_api_recipe_from_orm(orm_recipe: RecipeSaModel) -> ApiRecipe:
    """Convert ORM Recipe to ApiRecipe using from_orm_model method"""
    return ApiRecipe.from_orm_model(orm_recipe)


# =============================================================================
# JSON VALIDATION AND EDGE CASE TESTING
# =============================================================================

def create_valid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various valid JSON test cases for model_validate_json testing"""
    return [
        # Simple recipe
        {
            "id": str(uuid4()),
            "name": "Simple Recipe",
            "description": "A simple test recipe",
            "instructions": "1. Mix ingredients. 2. Cook. 3. Serve.",
            "author_id": generate_deterministic_id("author-1"),
            "meal_id": str(uuid4()),
            "ingredients": [
                {"name": "Ingredient 1", "quantity": 1.0, "unit": "g", "position": 0, "full_text": "1 unit of ingredient 1", "product_id": None}
            ],
            "tags": [
                {"key": "difficulty", "value": "easy", "author_id": generate_deterministic_id("author-1"), "type": "recipe"}
            ],
            "ratings": [
                {"user_id": str(uuid4()), "recipe_id": str(uuid4()), "taste": 5, "convenience": 5, "comment": "Great!"}
            ],
            "privacy": "public",
            "nutri_facts": {"calories": 100.0, "protein": 5.0, "carbohydrate": 15.0, "total_fat": 2.0},
            "total_time": 30,
            "weight_in_grams": 200,
            "image_url": "https://example.com/recipe.jpg",
            "average_taste_rating": 5.0,
            "average_convenience_rating": 5.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "discarded": False,
            "version": 1
        },
        # Complex recipe with many nested objects
        {
            "id": str(uuid4()),
            "name": "Complex Recipe",
            "description": "A complex test recipe with many components",
            "instructions": "Complex multi-step instructions...",
            "author_id": generate_deterministic_id("author-2"),
            "meal_id": str(uuid4()),
            "ingredients": [
                {"name": f"Ingredient {i}", "quantity": float(i), "unit": "l", "position": i-1, "full_text": f"{i}g of ingredient {i}", "product_id": str(uuid4())}
                for i in range(1, 11)
            ],
            "tags": [
                {"key": "cuisine", "value": "italian", "author_id": generate_deterministic_id("author-2"), "type": "recipe"},
                {"key": "difficulty", "value": "hard", "author_id": generate_deterministic_id("author-2"), "type": "recipe"}
            ],
            "ratings": [
                {"user_id": str(uuid4()), "recipe_id": str(uuid4()), "taste": i, "convenience": 6-i, "comment": f"Rating {i}"}
                for i in range(1, 6)
            ],
            "privacy": "private",
            "nutri_facts": {"calories": 500.0, "protein": 25.0, "carbohydrate": 50.0, "total_fat": 20.0, "sodium": 800.0},
            "total_time": 120,
            "weight_in_grams": 800,
            "utensils": "Various kitchen tools",
            "notes": "Detailed cooking notes",
            "image_url": "https://example.com/complex-recipe.jpg",
            "average_taste_rating": 3.0,
            "average_convenience_rating": 3.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "discarded": False,
            "version": 1
        },
        # Minimal recipe (only required fields)
        {
            "id": str(uuid4()),
            "name": "Minimal Recipe",
            "instructions": "Cook it.",
            "author_id": str(uuid4()),
            "meal_id": str(uuid4()),
            "ingredients": [],
            "tags": [],
            "ratings": [],
            "privacy": "private",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "discarded": False,
            "version": 1
        }
    ]


def create_invalid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various invalid JSON test cases for validation error testing"""
    return [
        # Missing required fields
        {
            "data": {
                "id": str(uuid4()),
                "name": "Incomplete Recipe",
                # Missing instructions, author_id, meal_id
            },
            "expected_errors": ["instructions", "author_id", "meal_id"]
        },
        # Invalid field types
        {
            "data": {
                "id": str(uuid4()),
                "name": "Invalid Types Recipe",
                "instructions": "Cook it.",
                "author_id": str(uuid4()),
                "meal_id": str(uuid4()),
                "ingredients": "not a list",  # Should be list (will be converted to frozenset)
                "total_time": "not a number",  # Should be int
                "average_taste_rating": "not a number",  # Should be float
            },
            "expected_errors": ["ingredients", "total_time", "average_taste_rating"]
        },
        # Invalid rating values
        {
            "data": {
                "id": str(uuid4()),
                "name": "Invalid Rating Recipe",
                "instructions": "Cook it.",
                "author_id": str(uuid4()),
                "meal_id": str(uuid4()),
                "average_taste_rating": 6.0,  # Should be ≤ 5
                "average_convenience_rating": -1.0,  # Should be ≥ 0
            },
            "expected_errors": ["average_taste_rating", "average_convenience_rating"]
        },
        # Invalid nested objects
        {
            "data": {
                "id": str(uuid4()),
                "name": "Invalid Nested Recipe",
                "instructions": "Cook it.",
                "author_id": str(uuid4()),
                "meal_id": str(uuid4()),
                "ingredients": [
                    {"name": "Invalid Ingredient", "quantity": -1.0, "unit": "invalid_unit", "position": 0}  # Fixed: use valid position, invalid quantity/unit
                ],
                "ratings": [
                    {"user_id": "not-a-uuid", "recipe_id": str(uuid4()), "taste": 6, "convenience": 5}  # Invalid user_id, taste > 5
                ],
            },
            "expected_errors": ["ingredients", "ratings"]
        },
        # Author id does not match the tag author_id
        {
            "data": {
                "id": str(uuid4()),
                "name": "Invalid Tag Author Recipe",
                "instructions": "Cook it.",
                "author_id": str(uuid4()),
                "meal_id": str(uuid4()),
                "tags": [
                    {"key": "cuisine", "value": "italian", "author_id": str(uuid4()), "type": "recipe"}
                ]
            },
            "expected_errors": ["tags"]
        }
    ]


def validate_average_rating_correction_roundtrip(api_recipe: ApiRecipe) -> tuple[bool, Dict[str, Any]]:
    """
    Test that incorrect average ratings are corrected during domain round-trip.
    
    This tests the edge case where JSON contains incorrect average ratings.
    The domain model should compute correct values, and when converted back to API,
    the averages should be corrected.
    
    Returns:
        Tuple of (success, details) where details contains original and corrected values
    """
    # Convert to domain (this should trigger computation of correct averages)
    domain_recipe = api_recipe.to_domain()
    
    # Convert back to API (this should have corrected averages)
    corrected_api_recipe = ApiRecipe.from_domain(domain_recipe)
    
    # Calculate expected averages from ratings
    if api_recipe.ratings is not None:
        expected_taste_avg = sum(r.taste for r in api_recipe.ratings) / len(api_recipe.ratings)
        expected_convenience_avg = sum(r.convenience for r in api_recipe.ratings) / len(api_recipe.ratings)
    else:
        expected_taste_avg = None
        expected_convenience_avg = None
    
    # Check if correction occurred
    taste_corrected = corrected_api_recipe.average_taste_rating == expected_taste_avg
    convenience_corrected = corrected_api_recipe.average_convenience_rating == expected_convenience_avg
    
    details = {
        "original_taste_avg": api_recipe.average_taste_rating,
        "corrected_taste_avg": corrected_api_recipe.average_taste_rating,
        "expected_taste_avg": expected_taste_avg,
        "original_convenience_avg": api_recipe.average_convenience_rating,
        "corrected_convenience_avg": corrected_api_recipe.average_convenience_rating,
        "expected_convenience_avg": expected_convenience_avg,
        "taste_corrected": taste_corrected,
        "convenience_corrected": convenience_corrected
    }
    
    return (taste_corrected and convenience_corrected), details


# =============================================================================
# PERFORMANCE TESTING HELPERS
# =============================================================================

def create_bulk_api_recipe_creation_dataset(count: int = 1000) -> List[Dict[str, Any]]:
    """Create a dataset for bulk recipe creation performance testing"""
    return [create_api_recipe_kwargs() for _ in range(count)]


def create_bulk_json_serialization_dataset(count: int = 1000) -> List[str]:
    """Create a dataset for bulk JSON serialization performance testing"""
    recipes = [create_api_recipe() for _ in range(count)]
    return [recipe.model_dump_json() for recipe in recipes]


def create_bulk_json_deserialization_dataset(count: int = 1000) -> List[str]:
    """Create a dataset for bulk JSON deserialization performance testing"""
    json_strings = []
    for _ in range(count):
        recipe_kwargs = create_api_recipe_kwargs()
        recipe_kwargs = _convert_to_json_serializable(recipe_kwargs)
        json_strings.append(json.dumps(recipe_kwargs))
    return json_strings


def create_conversion_performance_dataset_for_api_recipe(count: int = 1000) -> Dict[str, Any]:
    """Create a dataset for conversion performance testing"""
    api_recipes = [create_api_recipe() for _ in range(count)]
    domain_recipes = [recipe.to_domain() for recipe in api_recipes[:count//2]]
    
    return {
        "api_recipes": api_recipes,
        "domain_recipes": domain_recipes,
        "total_count": count
    }


def create_nested_object_validation_dataset_for_api_recipe(count: int = 1000) -> List[ApiRecipe]:
    """Create a dataset for nested object validation performance testing"""
    recipes = []
    
    for i in range(count):
        # Get the recipe's author_id early so we can use it for tags
        author_id = str(uuid4())
        
        # Create recipes with varying complexity
        ingredient_count = (i % 20) + 1  # 1 to 20 ingredients
        rating_count = (i % 10) + 1      # 1 to 10 ratings
        tag_count = (i % 5) + 1          # 1 to 5 tags
        
        # Create frozensets instead of lists
        ingredients = frozenset([create_api_ingredient(position=j) for j in range(ingredient_count)])
        ratings = frozenset([create_api_rating() for _ in range(rating_count)])
        tags = frozenset([create_api_recipe_tag(author_id=author_id, post_fix=str(j)) for j in range(tag_count)])
        
        recipe = create_api_recipe(
            author_id=author_id,
            ingredients=ingredients,
            ratings=ratings,
            tags=tags
        )
        recipes.append(recipe)
    
    return recipes


# =============================================================================
# FIELD VALIDATION EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_invalid_name(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid name for validation testing"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", ""),  # Empty string should fail min_length=1
        **{k: v for k, v in kwargs.items() if k != "name"}
    )

def create_api_recipe_with_invalid_instructions(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid instructions for validation testing"""
    return create_api_recipe_kwargs(
        instructions=kwargs.get("instructions", ""),  # Empty string should fail min_length=1
        **{k: v for k, v in kwargs.items() if k != "instructions"}
    )

def create_api_recipe_with_invalid_total_time(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid total_time for validation testing"""
    return create_api_recipe_kwargs(
        total_time=kwargs.get("total_time", -1),  # Negative should fail validation
        **{k: v for k, v in kwargs.items() if k != "total_time"}
    )

def create_api_recipe_with_invalid_weight(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid weight for validation testing"""
    return create_api_recipe_kwargs(
        weight_in_grams=kwargs.get("weight_in_grams", -100),  # Negative should fail validation
        **{k: v for k, v in kwargs.items() if k != "weight_in_grams"}
    )

def create_api_recipe_with_invalid_taste_rating(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid taste rating for validation testing"""
    return create_api_recipe_kwargs(
        average_taste_rating=kwargs.get("average_taste_rating", 6.0),  # > 5 should fail validation
        **{k: v for k, v in kwargs.items() if k != "average_taste_rating"}
    )

def create_api_recipe_with_invalid_convenience_rating(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid convenience rating for validation testing"""
    return create_api_recipe_kwargs(
        average_convenience_rating=kwargs.get("average_convenience_rating", -1.0),  # < 0 should fail validation
        **{k: v for k, v in kwargs.items() if k != "average_convenience_rating"}
    )

def create_api_recipe_with_invalid_privacy(**kwargs) -> Dict[str, Any]:
    """Create recipe kwargs with invalid privacy for validation testing"""
    return create_api_recipe_kwargs(
        privacy=kwargs.get("privacy", "invalid_privacy"),  # Invalid enum value
        **{k: v for k, v in kwargs.items() if k != "privacy"}
    )

def create_api_recipe_with_boundary_values(**kwargs) -> Dict[str, Any]:
    """Create recipe with boundary values for testing limits"""
    return create_api_recipe_kwargs(
        total_time=kwargs.get("total_time", 0),  # Minimum valid value
        weight_in_grams=kwargs.get("weight_in_grams", 0),  # Minimum valid value
        average_taste_rating=kwargs.get("average_taste_rating", 0.0),  # Minimum valid rating
        average_convenience_rating=kwargs.get("average_convenience_rating", 5.0),  # Maximum valid rating
        **{k: v for k, v in kwargs.items() if k not in ["total_time", "weight_in_grams", "average_taste_rating", "average_convenience_rating"]}
    )

def create_api_recipe_with_extreme_boundary_values(**kwargs) -> Dict[str, Any]:
    """Create recipe with extreme boundary values for testing limits"""
    return create_api_recipe_kwargs(
        total_time=kwargs.get("total_time", 2147483647),  # Max int32
        weight_in_grams=kwargs.get("weight_in_grams", 2147483647),  # Max int32
        average_taste_rating=kwargs.get("average_taste_rating", 5.0),  # Maximum valid rating
        average_convenience_rating=kwargs.get("average_convenience_rating", 0.0),  # Minimum valid rating
        **{k: v for k, v in kwargs.items() if k not in ["total_time", "weight_in_grams", "average_taste_rating", "average_convenience_rating"]}
    )

def create_api_recipe_with_none_values(**kwargs) -> Dict[str, Any]:
    """Create recipe with None values for optional fields"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", None),
        instructions=kwargs.get("instructions", None),
        meal_id=kwargs.get("meal_id", None),
        ingredients=kwargs.get("ingredients", None),
        tags=kwargs.get("tags", None),
        privacy=kwargs.get("privacy", None),
        description=kwargs.get("description", None),
        utensils=kwargs.get("utensils", None),
        total_time=kwargs.get("total_time", None),
        notes=kwargs.get("notes", None),
        weight_in_grams=kwargs.get("weight_in_grams", None),
        image_url=kwargs.get("image_url", None),
        nutri_facts=kwargs.get("nutri_facts", None),
        **{k: v for k, v in kwargs.items() if k not in ["description", "utensils", "total_time", "notes", "weight_in_grams", "image_url", "average_taste_rating", "average_convenience_rating", "nutri_facts"]}
    )

def create_api_recipe_with_empty_strings(**kwargs) -> Dict[str, Any]:
    """Create recipe with empty strings for optional string fields"""
    return create_api_recipe_kwargs(
        description=kwargs.get("description", ""),
        utensils=kwargs.get("utensils", ""),
        notes=kwargs.get("notes", ""),
        image_url=kwargs.get("image_url", ""),
        **{k: v for k, v in kwargs.items() if k not in ["description", "utensils", "notes", "image_url"]}
    )

def create_api_recipe_with_whitespace_strings(**kwargs) -> Dict[str, Any]:
    """Create recipe with whitespace-only strings for string fields"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", "   "),  # Should be handled by validate_optional_text
        instructions=kwargs.get("instructions", "\t\n  "),  # Should be handled by validate_optional_text
        description=kwargs.get("description", "   "),
        utensils=kwargs.get("utensils", "\t\n"),
        notes=kwargs.get("notes", "   "),
        **{k: v for k, v in kwargs.items() if k not in ["name", "instructions", "description", "utensils", "notes"]}
    )

# =============================================================================
# TAGS VALIDATION EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_invalid_tag_dict(**kwargs) -> Dict[str, Any]:
    """Create recipe with invalid tag dictionary for validation testing"""
    return create_api_recipe_kwargs(
        tags=kwargs.get("tags", [
            {"key": "test", "value": "value"},  # Missing 'type' and 'author_id'
            {"key": "test2", "value": "value2", "type": "recipe"},  # Missing 'author_id'
        ]),
        **{k: v for k, v in kwargs.items() if k != "tags"}
    )

def create_api_recipe_with_invalid_tag_types(**kwargs) -> Dict[str, Any]:
    """Create recipe with invalid tag types for validation testing"""
    return create_api_recipe_kwargs(
        tags=kwargs.get("tags", [
            "invalid_string_tag",  # Should fail - not dict or ApiTag
            123,  # Should fail - not dict or ApiTag
            {"key": "test"},  # Should fail - missing required fields
        ]),
        **{k: v for k, v in kwargs.items() if k != "tags"}
    )

def create_api_recipe_with_tag_without_author_id_context(**kwargs) -> Dict[str, Any]:
    """Create recipe with tags missing author_id when author_id not in context"""
    recipe_kwargs = create_api_recipe_kwargs(**kwargs)
    # Remove author_id from main data to test the validation error path
    author_id = recipe_kwargs.pop("author_id", None)
    recipe_kwargs["tags"] = [
        {"key": "test", "value": "value", "type": "recipe"}  # Missing author_id and no context
    ]
    return recipe_kwargs

def create_api_recipe_with_mixed_tag_types(**kwargs) -> Dict[str, Any]:
    """Create recipe with mixed tag types for validation testing"""
    author_id = kwargs.get("author_id", str(uuid4()))
    return create_api_recipe_kwargs(
        author_id=author_id,
        tags=kwargs.get("tags", [
            create_api_recipe_tag(author_id=author_id,key="existing", value="tag"),  # Valid ApiTag
            {"key": "dict", "value": "tag", "type": "recipe", "author_id": author_id},  # Valid dict (missing author_id will be added)
        ]),
        **{k: v for k, v in kwargs.items() if k != "tags"}
    )

# =============================================================================
# FROZENSET VALIDATION EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_list_ingredients(**kwargs) -> Dict[str, Any]:
    """Create recipe with list instead of frozenset for ingredients"""
    ingredients = frozenset([create_api_ingredient(position=i) for i in range(3)])
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", ingredients),  # List instead of frozenset
        **{k: v for k, v in kwargs.items() if k != "ingredients"}
    )

def create_api_recipe_with_set_ingredients(**kwargs) -> Dict[str, Any]:
    """Create recipe with set instead of frozenset for ingredients"""
    ingredients = frozenset([create_api_ingredient(position=i) for i in range(3)])  # Use list since ApiIngredient is not hashable
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", ingredients),  # List instead of frozenset
        **{k: v for k, v in kwargs.items() if k != "ingredients"}
    )

def create_api_recipe_with_list_ratings(**kwargs) -> Dict[str, Any]:
    """Create recipe with list instead of frozenset for ratings"""
    ratings = frozenset([create_api_rating() for _ in range(3)])
    return create_api_recipe_kwargs(
        ratings=kwargs.get("ratings", ratings),  # List instead of frozenset
        **{k: v for k, v in kwargs.items() if k != "ratings"}
    )

def create_api_recipe_with_set_ratings(**kwargs) -> Dict[str, Any]:
    """Create recipe with set instead of frozenset for ratings"""
    ratings = frozenset([create_api_rating() for _ in range(3)])  # Use list since ApiRating is not hashable
    return create_api_recipe_kwargs(
        ratings=kwargs.get("ratings", ratings),  # List instead of frozenset
        **{k: v for k, v in kwargs.items() if k != "ratings"}
    )

def create_api_recipe_with_list_tags(**kwargs) -> Dict[str, Any]:
    """Create recipe with list instead of frozenset for tags"""
    author_id = kwargs.get("author_id", str(uuid4()))
    tags = frozenset([create_api_recipe_tag(author_id=author_id,post_fix=str(i)) for i in range(3)])
    return create_api_recipe_kwargs(
        author_id=author_id,
        tags=kwargs.get("tags", tags),  # List instead of frozenset
        **{k: v for k, v in kwargs.items() if k != "tags"}
    )

def create_api_recipe_with_set_tags(**kwargs) -> Dict[str, Any]:
    """Create recipe with set instead of frozenset for tags"""
    author_id = kwargs.get("author_id", str(uuid4()))
    tags = frozenset([create_api_recipe_tag(author_id=author_id,post_fix=str(i)) for i in range(3)])  # Use list since ApiTag is not hashable
    return create_api_recipe_kwargs(
        author_id=author_id,
        tags=kwargs.get("tags", tags),  # List instead of frozenset
        **{k: v for k, v in kwargs.items() if k != "tags"}
    )

def create_api_recipe_with_empty_collections(**kwargs) -> Dict[str, Any]:
    """Create recipe with empty collections for testing"""
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", frozenset()),
        ratings=kwargs.get("ratings", frozenset()),
        tags=kwargs.get("tags", frozenset()),
        **{k: v for k, v in kwargs.items() if k not in ["ingredients", "ratings", "tags"]}
    )

# =============================================================================
# DOMAIN RULE VALIDATION EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_invalid_ingredient_positions(**kwargs) -> Dict[str, Any]:
    """Create recipe with invalid ingredient positions for domain rule testing"""
    # Create ingredients with non-consecutive positions
    ingredients = frozenset([
        create_api_ingredient(position=0),
        create_api_ingredient(position=2),  # Gap in positions
        create_api_ingredient(position=5),  # Another gap
    ])
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", ingredients),
        **{k: v for k, v in kwargs.items() if k != "ingredients"}
    )

def create_api_recipe_with_negative_ingredient_positions(**kwargs) -> Dict[str, Any]:
    """Create recipe with negative ingredient positions for domain rule testing"""
    ingredients = frozenset([
        create_api_ingredient(position=-1),  # Negative position
        create_api_ingredient(position=0),
        create_api_ingredient(position=1),
    ])
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", ingredients),
        **{k: v for k, v in kwargs.items() if k != "ingredients"}
    )

def create_api_recipe_with_duplicate_ingredient_positions(**kwargs) -> Dict[str, Any]:
    """Create recipe with duplicate ingredient positions for domain rule testing"""
    ingredients = frozenset([
        create_api_ingredient(position=0),
        create_api_ingredient(position=0),  # Duplicate position
        create_api_ingredient(position=1),
    ])
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", ingredients),
        **{k: v for k, v in kwargs.items() if k != "ingredients"}
    )

def create_api_recipe_with_non_zero_start_positions(**kwargs) -> Dict[str, Any]:
    """Create recipe with ingredient positions not starting from 0"""
    ingredients = frozenset([
        create_api_ingredient(position=1),  # Should start from 0
        create_api_ingredient(position=2),
        create_api_ingredient(position=3),
    ])
    return create_api_recipe_kwargs(
        ingredients=kwargs.get("ingredients", ingredients),
        **{k: v for k, v in kwargs.items() if k != "ingredients"}
    )

def create_api_recipe_with_invalid_tag_author_id(**kwargs) -> Dict[str, Any]:
    """Create recipe with tags having different author_id than recipe author"""
    recipe_kwargs = create_api_recipe_kwargs(**kwargs)
    different_author_id = str(uuid4())
    
    # Ensure different author_id
    while different_author_id == recipe_kwargs["author_id"]:
        different_author_id = str(uuid4())
    
    recipe_kwargs["tags"] = frozenset([
        create_api_recipe_tag(author_id=different_author_id)  # Different author_id
    ])
    
    return recipe_kwargs

# =============================================================================
# COMPUTED PROPERTIES EDGE CASES - CRITICAL ADDITIONS  
# =============================================================================

def create_api_recipe_with_mismatched_computed_properties(**kwargs) -> Dict[str, Any]:
    """Create recipe with mismatched computed properties for testing corrections"""
    # Create ratings with known values
    ratings = frozenset([
        create_api_rating(taste=4, convenience=3),
        create_api_rating(taste=2, convenience=5),
        create_api_rating(taste=5, convenience=1),
    ])
    
    # True averages: taste=3.67, convenience=3.0
    # Provide incorrect averages
    return create_api_recipe_kwargs(
        ratings=ratings,
        average_taste_rating=kwargs.get("average_taste_rating", 1.0),  # Incorrect
        average_convenience_rating=kwargs.get("average_convenience_rating", 5.0),  # Incorrect
        **{k: v for k, v in kwargs.items() if k not in ["ratings", "average_taste_rating", "average_convenience_rating"]}
    )

def create_api_recipe_with_single_rating(**kwargs) -> Dict[str, Any]:
    """Create recipe with single rating for edge case testing"""
    rating = create_api_rating(taste=4, convenience=3)
    return create_api_recipe_kwargs(
        ratings=frozenset([rating]),
        average_taste_rating=kwargs.get("average_taste_rating", 4.0),
        average_convenience_rating=kwargs.get("average_convenience_rating", 3.0),
        **{k: v for k, v in kwargs.items() if k not in ["ratings", "average_taste_rating", "average_convenience_rating"]}
    )

def create_api_recipe_with_extreme_ratings(**kwargs) -> Dict[str, Any]:
    """Create recipe with extreme rating values for edge case testing"""
    ratings = frozenset([
        create_api_rating(taste=0, convenience=0),  # Minimum values
        create_api_rating(taste=5, convenience=5),  # Maximum values
    ])
    return create_api_recipe_kwargs(
        ratings=ratings,
        average_taste_rating=kwargs.get("average_taste_rating", 2.5),
        average_convenience_rating=kwargs.get("average_convenience_rating", 2.5),
        **{k: v for k, v in kwargs.items() if k not in ["ratings", "average_taste_rating", "average_convenience_rating"]}
    )

def create_api_recipe_with_fractional_averages(**kwargs) -> Dict[str, Any]:
    """Create recipe with fractional average ratings for precision testing"""
    ratings = frozenset([
        create_api_rating(taste=1, convenience=1),
        create_api_rating(taste=2, convenience=2),
        create_api_rating(taste=3, convenience=3),
    ])
    # Averages: taste=2.0, convenience=2.0
    return create_api_recipe_kwargs(
        ratings=ratings,
        average_taste_rating=kwargs.get("average_taste_rating", 2.0),
        average_convenience_rating=kwargs.get("average_convenience_rating", 2.0),
        **{k: v for k, v in kwargs.items() if k not in ["ratings", "average_taste_rating", "average_convenience_rating"]}
    )

# =============================================================================
# DATETIME EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_future_timestamps(**kwargs) -> Dict[str, Any]:
    """Create recipe with future timestamps for edge case testing"""
    future_time = datetime.now() + timedelta(days=365)
    return create_api_recipe_kwargs(
        created_at=kwargs.get("created_at", future_time),
        updated_at=kwargs.get("updated_at", future_time + timedelta(hours=1)),
        **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
    )

def create_api_recipe_with_past_timestamps(**kwargs) -> Dict[str, Any]:
    """Create recipe with very old timestamps for edge case testing"""
    past_time = datetime(1900, 1, 1)
    return create_api_recipe_kwargs(
        created_at=kwargs.get("created_at", past_time),
        updated_at=kwargs.get("updated_at", past_time + timedelta(hours=1)),
        **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
    )

def create_api_recipe_with_invalid_timestamp_order(**kwargs) -> Dict[str, Any]:
    """Create recipe with updated_at before created_at for logic testing"""
    base_time = datetime.now()
    return create_api_recipe_kwargs(
        created_at=kwargs.get("created_at", base_time),
        updated_at=kwargs.get("updated_at", base_time - timedelta(hours=1)),  # Before created_at
        **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
    )

def create_api_recipe_with_same_timestamps(**kwargs) -> Dict[str, Any]:
    """Create recipe with identical created_at and updated_at for edge case testing"""
    same_time = datetime.now()
    return create_api_recipe_kwargs(
        created_at=kwargs.get("created_at", same_time),
        updated_at=kwargs.get("updated_at", same_time),
        **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
    )

# =============================================================================
# UNICODE AND SPECIAL CHARACTER EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_unicode_text(**kwargs) -> Dict[str, Any]:
    """Create recipe with unicode characters for internationalization testing"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", "Pâté de Foie Gras avec Échalotes 🍷"),
        description=kwargs.get("description", "Délicieux pâté français avec des échalotes caramélisées et une touche de cognac. Parfait pour les occasions spéciales! 🇫🇷"),
        instructions=kwargs.get("instructions", "1. Nettoyer les échalotes 🧅\n2. Caraméliser à feu doux 🔥\n3. Ajouter le cognac 🍾\n4. Servir avec du pain grillé 🍞"),
        notes=kwargs.get("notes", "Conseil: Utiliser des échalotes de qualité supérieure pour un meilleur goût! 👨‍🍳"),
        utensils=kwargs.get("utensils", "Couteau de chef, poêle anti-adhésive, cuillère en bois"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "notes", "utensils"]}
    )

def create_api_recipe_with_special_characters(**kwargs) -> Dict[str, Any]:
    """Create recipe with special characters for validation testing"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", "Recipe with Special !@#$%^&*()_+ Characters"),
        description=kwargs.get("description", "Testing <>&\"'{}[]|\\ special chars"),
        instructions=kwargs.get("instructions", "1. Mix & match 2. Heat @ 350°F 3. Serve w/ style!"),
        notes=kwargs.get("notes", "Note: Be careful with temp. measurements (°F vs °C)"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "notes"]}
    )

def create_api_recipe_with_html_characters(**kwargs) -> Dict[str, Any]:
    """Create recipe with HTML characters for XSS testing"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", "Recipe with <script>alert('XSS')</script> HTML"),
        description=kwargs.get("description", "<b>Bold</b> and <i>italic</i> text with <a href='#'>links</a>"),
        instructions=kwargs.get("instructions", "1. <strong>Strongly</strong> mix ingredients 2. <em>Emphasize</em> cooking time"),
        notes=kwargs.get("notes", "<!-- HTML comment --> <div>Div content</div>"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "notes"]}
    )

def create_api_recipe_with_sql_injection(**kwargs) -> Dict[str, Any]:
    """Create recipe with SQL injection attempts for security testing"""
    return create_api_recipe_kwargs(
        name=kwargs.get("name", "Recipe'; DROP TABLE recipes; --"),
        description=kwargs.get("description", "Description' OR '1'='1"),
        instructions=kwargs.get("instructions", "1. SELECT * FROM ingredients WHERE name = 'test' OR 1=1; --"),
        notes=kwargs.get("notes", "Notes\"; DELETE FROM recipes; --"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "notes"]}
    )

def create_api_recipe_with_very_long_text(**kwargs) -> Dict[str, Any]:
    """Create recipe with very long text for length limit testing"""
    long_text = "A" * 10000  # 10KB text
    return create_api_recipe_kwargs(
        name=kwargs.get("name", "Very Long Recipe Name " + "A" * (1000-23)),
        description=kwargs.get("description", "Very long description: " + long_text),
        instructions=kwargs.get("instructions", "Very long instructions: " + long_text),
        notes=kwargs.get("notes", "Very long notes: " + long_text),
        utensils=kwargs.get("utensils", "Very long utensils list: " + long_text),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "notes", "utensils"]}
    )

# =============================================================================
# CONCURRENCY AND THREAD SAFETY EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_concurrent_modifications(**kwargs) -> Dict[str, Any]:
    """Create recipe data that simulates concurrent modification scenarios"""
    # Create recipe with version conflicts
    return create_api_recipe_kwargs(
        version=kwargs.get("version", 1),
        created_at=kwargs.get("created_at", datetime.now()),
        updated_at=kwargs.get("updated_at", datetime.now() + timedelta(microseconds=1)),  # Very small time difference
        **{k: v for k, v in kwargs.items() if k not in ["version", "created_at", "updated_at"]}
    )

def create_api_recipe_with_high_version(**kwargs) -> Dict[str, Any]:
    """Create recipe with high version number for testing version handling"""
    return create_api_recipe_kwargs(
        version=kwargs.get("version", 99999),
        **{k: v for k, v in kwargs.items() if k != "version"}
    )

def create_api_recipe_with_zero_version(**kwargs) -> Dict[str, Any]:
    """Create recipe with zero version for edge case testing"""
    return create_api_recipe_kwargs(
        version=kwargs.get("version", 0),
        **{k: v for k, v in kwargs.items() if k != "version"}
    )

def create_api_recipe_with_negative_version(**kwargs) -> Dict[str, Any]:
    """Create recipe with negative version for validation testing"""
    return create_api_recipe_kwargs(
        version=kwargs.get("version", -1),
        **{k: v for k, v in kwargs.items() if k != "version"}
    )

# =============================================================================
# COMPREHENSIVE VALIDATION FUNCTIONS - CRITICAL ADDITIONS
# =============================================================================

def create_comprehensive_validation_test_cases_for_api_recipe() -> List[Dict[str, Any]]:
    """Create comprehensive validation test cases covering all edge cases"""
    return [
        # Field validation edge cases
        {"factory": create_api_recipe_with_invalid_name, "expected_error": "name"}, # 0
        {"factory": create_api_recipe_with_invalid_instructions, "expected_error": "instructions"}, # 1
        {"factory": create_api_recipe_with_invalid_total_time, "expected_error": "total_time"}, # 2
        {"factory": create_api_recipe_with_invalid_weight, "expected_error": "weight_in_grams"}, # 3
        {"factory": create_api_recipe_with_invalid_privacy, "expected_error": "privacy"}, # 4
        
        # Boundary cases
        {"factory": create_api_recipe_with_boundary_values, "expected_error": None}, # 5
        {"factory": create_api_recipe_with_extreme_boundary_values, "expected_error": None}, # 6
        {"factory": create_api_recipe_with_none_values, "expected_error": "name, instructions, meal_id"}, # 7
        {"factory": create_api_recipe_with_empty_strings, "expected_error": None}, # 8
        
        # Tags validation edge cases
        {"factory": create_api_recipe_with_invalid_tag_dict, "expected_error": "tags"},  # 9
        {"factory": create_api_recipe_with_invalid_tag_types, "expected_error": "tags"}, # 10
        {"factory": create_api_recipe_with_tag_without_author_id_context, "expected_error": "tags"}, # 11
        {"factory": create_api_recipe_with_mixed_tag_types, "expected_error": None}, # 12
        
        # Collection type edge cases
        {"factory": create_api_recipe_with_list_ingredients, "expected_error": None}, # 13
        {"factory": create_api_recipe_with_set_ingredients, "expected_error": None}, # 14
        {"factory": create_api_recipe_with_list_ratings, "expected_error": None}, # 15
        {"factory": create_api_recipe_with_set_ratings, "expected_error": None}, # 16
        {"factory": create_api_recipe_with_list_tags, "expected_error": None}, # 17
        {"factory": create_api_recipe_with_set_tags, "expected_error": None}, # 18
        {"factory": create_api_recipe_with_empty_collections, "expected_error": None}, # 19
       
        # Computed properties edge cases
        {"factory": create_api_recipe_with_mismatched_computed_properties, "expected_error": None}, # 20
        {"factory": create_api_recipe_with_single_rating, "expected_error": None}, # 21
        {"factory": create_api_recipe_with_extreme_ratings, "expected_error": None}, # 22
        {"factory": create_api_recipe_with_fractional_averages, "expected_error": None}, # 23
        
        # Datetime edge cases
        {"factory": create_api_recipe_with_future_timestamps, "expected_error": None}, # 24
        {"factory": create_api_recipe_with_past_timestamps, "expected_error": None}, # 25
        {"factory": create_api_recipe_with_invalid_timestamp_order, "expected_error": None}, # 26
        {"factory": create_api_recipe_with_same_timestamps, "expected_error": None}, # 27
        
        # Text edge cases
        {"factory": create_api_recipe_with_unicode_text, "expected_error": None}, # 28
        {"factory": create_api_recipe_with_special_characters, "expected_error": None}, # 29
        {"factory": create_api_recipe_with_html_characters, "expected_error": None}, # 30
        {"factory": create_api_recipe_with_sql_injection, "expected_error": None}, # 31
        {"factory": create_api_recipe_with_very_long_text, "expected_error": "validation"}, # 32
        
        # Concurrency edge cases
        {"factory": create_api_recipe_with_concurrent_modifications, "expected_error": None}, # 33
        {"factory": create_api_recipe_with_high_version, "expected_error": None} # 34
    ]

def validate_round_trip_conversion_for_api_recipe(api_recipe: ApiRecipe) -> Dict[str, Any]:
    """
    Comprehensive validation of round-trip conversion: API -> Domain -> API
    
    Tests all conversion methods and validates data integrity.
    """
    results = {
        "api_to_domain_success": False,
        "domain_to_api_success": False,
        "data_integrity_maintained": False,
        "computed_properties_corrected": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        if isinstance(api_recipe, dict):
            api_recipe = ApiRecipe(**api_recipe)
        # Test API -> Domain conversion
        domain_recipe = api_recipe.to_domain()
        results["api_to_domain_success"] = True
        
        # Test Domain -> API conversion
        converted_api_recipe = ApiRecipe.from_domain(domain_recipe)
        results["domain_to_api_success"] = True
        
        # Validate data integrity
        integrity_check = _validate_data_integrity(api_recipe, converted_api_recipe)
        results["data_integrity_maintained"] = integrity_check["maintained"]
        results["warnings"].extend(integrity_check["warnings"])
        
        # Validate computed properties correction
        computed_check = _validate_computed_properties_correction(api_recipe, converted_api_recipe)
        results["computed_properties_corrected"] = computed_check["corrected"]
        results["warnings"].extend(computed_check["warnings"])
        
    except Exception as e:
        results["errors"].append(f"Conversion failed: {str(e)}")
    
    return results

def _validate_data_integrity(original: ApiRecipe, converted: ApiRecipe) -> Dict[str, Any]:
    """Validate that core data is maintained during conversion"""
    warnings = []
    
    # Check required fields
    if original.name != converted.name:
        warnings.append("Name changed during conversion")
    if original.instructions != converted.instructions:
        warnings.append("Instructions changed during conversion")
    if original.author_id != converted.author_id:
        warnings.append("Author ID changed during conversion")
    if original.meal_id != converted.meal_id:
        warnings.append("Meal ID changed during conversion")
    
    # Check collections sizes
    assert original.ingredients is not None
    assert converted.ingredients is not None
    assert original.ratings is not None
    assert converted.ratings is not None
    assert original.tags is not None
    assert converted.tags is not None
    if len(original.ingredients) != len(converted.ingredients):
        warnings.append("Ingredients count changed during conversion")
    if len(original.ratings) != len(converted.ratings):
        warnings.append("Ratings count changed during conversion")
    if len(original.tags) != len(converted.tags):
        warnings.append("Tags count changed during conversion")
    
    return {
        "maintained": len(warnings) == 0,
        "warnings": warnings
    }

def _validate_computed_properties_correction(original: ApiRecipe, converted: ApiRecipe) -> Dict[str, Any]:
    """Validate that computed properties are corrected during conversion"""
    warnings = []
    
    # Calculate expected averages
    if original.ratings:
        expected_taste = sum(r.taste for r in original.ratings) / len(original.ratings)
        expected_convenience = sum(r.convenience for r in original.ratings) / len(original.ratings)
        
        # Check if conversion corrected the averages
        if converted.average_taste_rating != expected_taste:
            warnings.append(f"Taste average not corrected: expected {expected_taste}, got {converted.average_taste_rating}")
        if converted.average_convenience_rating != expected_convenience:
            warnings.append(f"Convenience average not corrected: expected {expected_convenience}, got {converted.average_convenience_rating}")
    
    return {
        "corrected": len(warnings) == 0,
        "warnings": warnings
    }

def validate_orm_conversion_for_api_recipe(api_recipe: ApiRecipe) -> Dict[str, Any]:
    """
    Comprehensive validation of ORM conversion: API -> ORM kwargs -> ORM -> API
    
    Tests ORM-related conversion methods.
    """
    results = {
        "api_to_orm_kwargs_success": False,
        "orm_kwargs_valid": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Test API -> ORM kwargs conversion
        orm_kwargs = api_recipe.to_orm_kwargs()
        results["api_to_orm_kwargs_success"] = True
        
        # Validate ORM kwargs structure
        validation_result = _validate_orm_kwargs_structure(orm_kwargs)
        results["orm_kwargs_valid"] = validation_result["valid"]
        results["warnings"].extend(validation_result["warnings"])
        
    except Exception as e:
        results["errors"].append(f"ORM conversion failed: {str(e)}")
    
    return results

def _validate_orm_kwargs_structure(orm_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ORM kwargs structure"""
    warnings = []
    required_fields = ["id", "name", "instructions", "author_id", "meal_id"]
    
    for field in required_fields:
        if field not in orm_kwargs:
            warnings.append(f"Missing required ORM field: {field}")
    
    # Check collection types
    if "ingredients" in orm_kwargs and not isinstance(orm_kwargs["ingredients"], list):
        warnings.append("Ingredients should be list in ORM kwargs")
    if "ratings" in orm_kwargs and not isinstance(orm_kwargs["ratings"], list):
        warnings.append("Ratings should be list in ORM kwargs")
    if "tags" in orm_kwargs and not isinstance(orm_kwargs["tags"], list):
        warnings.append("Tags should be list in ORM kwargs")
    
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings
    }

def validate_json_serialization_of_api_recipe(api_recipe: ApiRecipe) -> Dict[str, Any]:
    """
    Comprehensive validation of JSON serialization: API -> JSON -> API
    
    Tests JSON-related methods.
    """
    results = {
        "api_to_json_success": False,
        "json_to_api_success": False,
        "json_valid": False,
        "round_trip_success": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Test API -> JSON conversion
        json_string = api_recipe.model_dump_json()
        results["api_to_json_success"] = True
        
        # Validate JSON structure
        try:
            json_data = json.loads(json_string)
            results["json_valid"] = True
        except json.JSONDecodeError as e:
            results["errors"].append(f"Invalid JSON generated: {str(e)}")
            return results
        
        # Test JSON -> API conversion
        converted_api_recipe = ApiRecipe.model_validate_json(json_string)
        results["json_to_api_success"] = True
        
        # Validate round-trip integrity
        integrity_check = _validate_data_integrity(api_recipe, converted_api_recipe)
        results["round_trip_success"] = integrity_check["maintained"]
        results["warnings"].extend(integrity_check["warnings"])
        
    except Exception as e:
        results["errors"].append(f"JSON serialization failed: {str(e)}")
    
    return results

# =============================================================================
# PERFORMANCE AND STRESS TESTING EDGE CASES - CRITICAL ADDITIONS
# =============================================================================

def create_api_recipe_with_massive_collections(**kwargs) -> Dict[str, Any]:
    """Create recipe with massive collections for performance testing"""
    author_id = kwargs.get("author_id", str(uuid4()))
    # Create very large collections
    massive_ingredients = frozenset([create_api_ingredient(position=i) for i in range(100)])
    massive_ratings = frozenset([create_api_rating() for _ in range(1000)])
    massive_tags = frozenset([create_api_recipe_tag(author_id=author_id,post_fix=str(i)) for i in range(100)])
    
    return create_api_recipe_kwargs(
        author_id=author_id,
        ingredients=kwargs.get("ingredients", massive_ingredients),
        ratings=kwargs.get("ratings", massive_ratings),
        tags=kwargs.get("tags", massive_tags),
        **{k: v for k, v in kwargs.items() if k not in ["ingredients", "ratings", "tags"]}
    )

def create_api_recipe_with_deeply_nested_data(**kwargs) -> Dict[str, Any]:
    """Create recipe with deeply nested data structures for testing"""
    # Create complex nested nutrition facts
    complex_nutri_facts = create_api_nutri_facts(
        calories=999.99,
        protein=99.99,
        carbohydrate=999.99,
        total_fat=99.99,
        saturated_fat=49.99,
        trans_fat=0.99,
        sugar=199.99,
        sodium=2999.99,
        dietary_fiber=49.99
    )
    
    # Create complex ingredients with detailed information
    complex_ingredients = frozenset([
        create_api_ingredient(
            name=f"Complex Ingredient {i}",
            quantity=float(i+1 * 1.5),
            position=i,
            full_text=f"Detailed full text for ingredient {i} with lots of information and details"
        )
        for i in range(50)
    ])
    
    return create_api_recipe_kwargs(
        nutri_facts=kwargs.get("nutri_facts", complex_nutri_facts),
        ingredients=kwargs.get("ingredients", complex_ingredients),
        **{k: v for k, v in kwargs.items() if k not in ["nutri_facts", "ingredients"]}
    )

def create_stress_test_dataset_for_api_recipe(count: int = 10000) -> List[Dict[str, Any]]:
    """Create a large dataset for stress testing"""
    dataset = []
    
    for i in range(count):
        # Vary the complexity
        if i % 10 == 0:
            recipe_kwargs = create_api_recipe_with_massive_collections()
        elif i % 10 == 1:
            recipe_kwargs = create_api_recipe_with_deeply_nested_data()
        elif i % 10 == 2:
            recipe_kwargs = create_api_recipe_with_very_long_text()
        else:
            recipe_kwargs = create_api_recipe_kwargs()
        
        dataset.append(recipe_kwargs)
    
    return dataset