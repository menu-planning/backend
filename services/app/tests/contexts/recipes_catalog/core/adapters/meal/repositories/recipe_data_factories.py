"""
Data factories for RecipeRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different recipe types

All data follows the exact structure of Recipe domain entities and their relationships.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import uuid

from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_RECIPE_COUNTER = 1
_INGREDIENT_COUNTER = 1
_RATING_COUNTER = 1
_TAG_COUNTER = 1


def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _RECIPE_COUNTER, _INGREDIENT_COUNTER, _RATING_COUNTER, _TAG_COUNTER
    _RECIPE_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _RATING_COUNTER = 1
    _TAG_COUNTER = 1


# =============================================================================
# RECIPE DATA FACTORIES
# =============================================================================

def create_recipe_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create recipe kwargs with deterministic values and validation.
    
    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required recipe creation parameters
        
    Raises:
        ValueError: If invalid attribute combinations are provided
    """
    global _RECIPE_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Create basic nutri_facts for deterministic testing
    basic_nutri_facts = NutriFacts(
        calories=100.0 + (_RECIPE_COUNTER * 50),  # 150, 200, 250, etc.
        protein=10.0 + (_RECIPE_COUNTER * 2),     # 12, 14, 16, etc.
        carbohydrate=20.0 + (_RECIPE_COUNTER * 3), # 23, 26, 29, etc.
        total_fat=5.0 + (_RECIPE_COUNTER * 1.5),   # 6.5, 8.0, 9.5, etc.
    )
    
    # Create basic ingredients with deterministic data
    basic_ingredients = [
        Ingredient(
            name=f"Ingredient {_RECIPE_COUNTER}-1",
            unit=MeasureUnit.GRAM,
            quantity=100.0 + _RECIPE_COUNTER,
            position=0,
            full_text=f"100g of ingredient {_RECIPE_COUNTER}-1",
            product_id=f"product_{_RECIPE_COUNTER:03d}_1" if _RECIPE_COUNTER % 2 == 0 else None
        ),
        Ingredient(
            name=f"Ingredient {_RECIPE_COUNTER}-2", 
            unit=MeasureUnit.MILLILITER,
            quantity=50.0 + _RECIPE_COUNTER,
            position=1,
            full_text=f"50ml of ingredient {_RECIPE_COUNTER}-2",
            product_id=f"product_{_RECIPE_COUNTER:03d}_2" if _RECIPE_COUNTER % 3 == 0 else None
        )
    ]
    
    defaults = {
        "id": f"recipe_{_RECIPE_COUNTER:03d}",
        "name": f"Test Recipe {_RECIPE_COUNTER}",
        "author_id": f"author_{(_RECIPE_COUNTER % 5) + 1}",  # Cycle through 5 authors
        "meal_id": f"meal_{(_RECIPE_COUNTER % 10) + 1}",     # Cycle through 10 meals
        "instructions": f"Test instructions for recipe {_RECIPE_COUNTER}. Step 1: Prepare ingredients. Step 2: Cook thoroughly.",
        "total_time": (15 + (_RECIPE_COUNTER * 5)) if _RECIPE_COUNTER % 4 != 0 else None,  # 20, 25, 30, None, 35, etc.
        "description": f"Test recipe description {_RECIPE_COUNTER}" if _RECIPE_COUNTER % 3 != 0 else None,
        "utensils": f"pot, pan, spoon" if _RECIPE_COUNTER % 2 == 0 else None,
        "notes": f"Test notes for recipe {_RECIPE_COUNTER}" if _RECIPE_COUNTER % 4 != 0 else None,
        "privacy": Privacy.PUBLIC if _RECIPE_COUNTER % 3 == 0 else Privacy.PRIVATE,  # Mix of public/private for access control testing
        "weight_in_grams": (200 + (_RECIPE_COUNTER * 50)) if _RECIPE_COUNTER % 3 != 0 else None,
        "image_url": f"https://example.com/recipe_{_RECIPE_COUNTER}.jpg" if _RECIPE_COUNTER % 2 == 0 else None,
        "created_at": base_time + timedelta(hours=_RECIPE_COUNTER),
        "updated_at": base_time + timedelta(hours=_RECIPE_COUNTER, minutes=30),
        "discarded": False,
        "version": 1,
        "ingredients": basic_ingredients,
        "tags": set(),  # Will be populated separately if needed
        "ratings": [],  # Will be populated separately if needed
        "nutri_facts": basic_nutri_facts,
        # Rating fields for filtering tests
        "average_taste_rating": None,  # Computed from ratings
        "average_convenience_rating": None,  # Computed from ratings
    }
    
    # Override with provided kwargs
    defaults.update(kwargs)
    
    # Validation logic to ensure required attributes
    required_fields = ["id", "name", "author_id", "meal_id", "instructions"]
    for field in required_fields:
        if not defaults.get(field):
            raise ValueError(f"Required field '{field}' cannot be empty")
    
    # Validate author_id format
    if not isinstance(defaults["author_id"], str) or not defaults["author_id"]:
        raise ValueError("author_id must be a non-empty string")
    
    # Validate meal_id format
    if not isinstance(defaults["meal_id"], str) or not defaults["meal_id"]:
        raise ValueError("meal_id must be a non-empty string")
    
    # Validate ingredients list
    if not isinstance(defaults["ingredients"], list) or len(defaults["ingredients"]) == 0:
        raise ValueError("ingredients must be a non-empty list")
    
    # Validate privacy enum
    if defaults["privacy"] not in [Privacy.PUBLIC, Privacy.PRIVATE]:
        raise ValueError("privacy must be Privacy.PUBLIC or Privacy.PRIVATE")
    
    # Increment counter for next call
    _RECIPE_COUNTER += 1
    
    return defaults


def create_recipe(**kwargs) -> _Recipe:
    """
    Create a Recipe domain entity with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity
    """
    recipe_kwargs = create_recipe_kwargs(**kwargs)
    return _Recipe(**recipe_kwargs)


# =============================================================================
# INGREDIENT DATA FACTORIES
# =============================================================================

def create_ingredient_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ingredient kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ingredient creation parameters
    """
    global _INGREDIENT_COUNTER
    
    # Predefined ingredient data for realistic testing
    ingredient_names = ["Flour", "Sugar", "Eggs", "Milk", "Butter", "Salt", "Pepper", "Olive Oil", "Onion", "Garlic"]
    units = [MeasureUnit.GRAM, MeasureUnit.MILLILITER, MeasureUnit.UNIT, MeasureUnit.TABLESPOON, MeasureUnit.TEASPOON]
    
    name = ingredient_names[(_INGREDIENT_COUNTER - 1) % len(ingredient_names)]
    unit = units[(_INGREDIENT_COUNTER - 1) % len(units)]
    
    defaults = {
        "name": f"{name}",
        "unit": unit,
        "quantity": 50.0 + (_INGREDIENT_COUNTER * 10),
        "position": (_INGREDIENT_COUNTER - 1) % 10,  # Keep positions reasonable
        "full_text": f"{50 + (_INGREDIENT_COUNTER * 10)}{unit.value} of {name.lower()}",
        "product_id": f"product_{_INGREDIENT_COUNTER:03d}" if _INGREDIENT_COUNTER % 2 == 0 else None,
    }
    
    defaults.update(kwargs)
    
    # Validation
    required_fields = ["name", "unit", "quantity", "position"]
    for field in required_fields:
        if defaults.get(field) is None:
            raise ValueError(f"Required ingredient field '{field}' cannot be None")
    
    if not isinstance(defaults["quantity"], (int, float)) or defaults["quantity"] <= 0:
        raise ValueError("quantity must be a positive number")
    
    if not isinstance(defaults["position"], int) or defaults["position"] < 0:
        raise ValueError("position must be a non-negative integer")
    
    _INGREDIENT_COUNTER += 1
    return defaults


def create_ingredient(**kwargs) -> Ingredient:
    """
    Create an Ingredient value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Ingredient value object
    """
    ingredient_kwargs = create_ingredient_kwargs(**kwargs)
    return Ingredient(**ingredient_kwargs)


# =============================================================================
# RATING DATA FACTORIES
# =============================================================================

def create_rating_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create rating kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with rating creation parameters
    """
    global _RATING_COUNTER
    
    # Ensure ratings are in valid range (0-5)
    taste_score = (_RATING_COUNTER % 6)  # 0, 1, 2, 3, 4, 5, 0, 1, ...
    convenience_score = ((_RATING_COUNTER + 2) % 6)  # 2, 3, 4, 5, 0, 1, 2, 3, ...
    
    defaults = {
        "user_id": f"user_{((_RATING_COUNTER - 1) % 5) + 1}",  # Cycle through 5 users
        "recipe_id": f"recipe_{((_RATING_COUNTER - 1) % 10) + 1}",  # Cycle through 10 recipes
        "taste": taste_score,
        "convenience": convenience_score,
        "comment": f"Test comment {_RATING_COUNTER}" if _RATING_COUNTER % 3 != 0 else None,
    }
    
    defaults.update(kwargs)
    
    # Validation
    required_fields = ["user_id", "recipe_id", "taste", "convenience"]
    for field in required_fields:
        if defaults.get(field) is None:
            raise ValueError(f"Required rating field '{field}' cannot be None")
    
    # Validate rating ranges (0-5)
    for rating_field in ["taste", "convenience"]:
        value = defaults[rating_field]
        if not isinstance(value, int) or value < 0 or value > 5:
            raise ValueError(f"{rating_field} must be an integer between 0 and 5")
    
    _RATING_COUNTER += 1
    return defaults


def create_rating(**kwargs) -> Rating:
    """
    Create a Rating value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Rating value object
    """
    rating_kwargs = create_rating_kwargs(**kwargs)
    return Rating(**rating_kwargs)


# =============================================================================
# TAG DATA FACTORIES
# =============================================================================

def create_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag kwargs with deterministic values for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # Predefined tag types for realistic recipe test data
    keys = ["cuisine", "diet", "difficulty", "meal_type", "cooking_method"]
    values_by_key = {
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "gluten-free"],
        "difficulty": ["easy", "medium", "hard"],
        "meal_type": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "cooking_method": ["baked", "grilled", "fried", "steamed", "raw"]
    }
    
    key = keys[(_TAG_COUNTER - 1) % len(keys)]
    value = values_by_key[key][(_TAG_COUNTER - 1) % len(values_by_key[key])]
    
    defaults = {
        "key": key,
        "value": value,
        "author_id": f"author_{((_TAG_COUNTER - 1) % 5) + 1}",
        "type": "recipe"  # Always recipe type for recipe tags
    }
    
    defaults.update(kwargs)
    
    # Validation
    required_fields = ["key", "value", "author_id", "type"]
    for field in required_fields:
        if not defaults.get(field):
            raise ValueError(f"Required tag field '{field}' cannot be empty")
    
    _TAG_COUNTER += 1
    return defaults


def create_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object
    """
    tag_kwargs = create_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)


# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

def get_recipe_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing recipe filtering.
    
    Returns:
        List of test scenarios with recipe_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "total_time_gte_match",
            "recipe_kwargs": {"name": "Long Cooking Recipe", "total_time": 60},
            "filter": {"total_time_gte": 45},
            "should_match": True,
            "description": "Recipe with 60min total_time should match gte filter of 45min"
        },
        {
            "scenario_id": "total_time_lte_match",
            "recipe_kwargs": {"name": "Quick Recipe", "total_time": 15},
            "filter": {"total_time_lte": 30},
            "should_match": True,
            "description": "Recipe with 15min total_time should match lte filter of 30min"
        },
        {
            "scenario_id": "total_time_range_match",
            "recipe_kwargs": {"name": "Medium Recipe", "total_time": 25},
            "filter": {"total_time_gte": 20, "total_time_lte": 30},
            "should_match": True,
            "description": "Recipe with 25min total_time should match range filter 20-30min"
        },
        {
            "scenario_id": "privacy_public_match",
            "recipe_kwargs": {"name": "Public Recipe", "privacy": Privacy.PUBLIC},
            "filter": {"privacy": "public"},
            "should_match": True,
            "description": "Public recipe should match privacy filter"
        },
        {
            "scenario_id": "privacy_private_match",
            "recipe_kwargs": {"name": "Private Recipe", "privacy": Privacy.PRIVATE},
            "filter": {"privacy": "private"},
            "should_match": True,
            "description": "Private recipe should match privacy filter"
        },
        {
            "scenario_id": "author_id_match",
            "recipe_kwargs": {"name": "Author Recipe", "author_id": "test_author_123"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Recipe should match author_id filter"
        },
        {
            "scenario_id": "meal_id_match",
            "recipe_kwargs": {"name": "Meal Recipe", "meal_id": "test_meal_456"},
            "filter": {"meal_id": "test_meal_456"},
            "should_match": True,
            "description": "Recipe should match meal_id filter"
        },
        {
            "scenario_id": "calories_gte_match",
            "recipe_kwargs": {
                "name": "High Calorie Recipe",
                "nutri_facts": NutriFacts(calories=500.0, protein=20.0, carbohydrate=40.0, total_fat=15.0)
            },
            "filter": {"calories_gte": 400.0},
            "should_match": True,
            "description": "Recipe with 500 calories should match gte filter of 400"
        },
        {
            "scenario_id": "protein_gte_match", 
            "recipe_kwargs": {
                "name": "High Protein Recipe",
                "nutri_facts": NutriFacts(calories=300.0, protein=30.0, carbohydrate=20.0, total_fat=10.0)
            },
            "filter": {"protein_gte": 25.0},
            "should_match": True,
            "description": "Recipe with 30g protein should match gte filter of 25g"
        },
        {
            "scenario_id": "weight_range_match",
            "recipe_kwargs": {"name": "Medium Weight Recipe", "weight_in_grams": 300},
            "filter": {"weight_in_grams_gte": 200, "weight_in_grams_lte": 400},
            "should_match": True,
            "description": "Recipe with 300g weight should match range filter 200-400g"
        }
    ]


def get_ingredient_relationship_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing ingredient relationships.
    
    Returns:
        List of test scenarios for ingredient filtering and relationships
    """
    return [
        {
            "scenario_id": "single_product_ingredient",
            "recipe_kwargs": {
                "name": "Recipe with Product Ingredient",
                "ingredients": [
                    Ingredient(
                        name="Test Flour",
                        unit=MeasureUnit.GRAM,
                        quantity=200.0,
                        position=0,
                        full_text="200g of test flour",
                        product_id="flour_product_123"
                    )
                ]
            },
            "filter": {"products": ["flour_product_123"]},
            "should_match": True,
            "description": "Recipe should match when filtering by ingredient product ID"
        },
        {
            "scenario_id": "multiple_product_ingredients",
            "recipe_kwargs": {
                "name": "Recipe with Multiple Products",
                "ingredients": [
                    Ingredient(name="Flour", unit=MeasureUnit.GRAM, quantity=200.0, position=0, product_id="flour_123"),
                    Ingredient(name="Sugar", unit=MeasureUnit.GRAM, quantity=100.0, position=1, product_id="sugar_456"),
                ]
            },
            "filter": {"products": ["flour_123", "sugar_456"]},
            "should_match": True,
            "description": "Recipe should match when filtering by multiple product IDs"
        },
        {
            "scenario_id": "ingredient_without_product",
            "recipe_kwargs": {
                "name": "Recipe with Generic Ingredient",
                "ingredients": [
                    Ingredient(name="Salt", unit=MeasureUnit.TEASPOON, quantity=1.0, position=0, product_id=None)
                ]
            },
            "filter": {"products": ["salt_product_789"]},
            "should_match": False,
            "description": "Recipe with generic ingredient (no product_id) should not match product filter"
        }
    ]


def get_rating_aggregation_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing rating aggregation.
    
    Returns:
        List of test scenarios for rating filtering and aggregation
    """
    return [
        {
            "scenario_id": "high_taste_rating",
            "recipe_kwargs": {
                "name": "Highly Rated Recipe",
                "ratings": [
                    Rating(user_id="user_1", recipe_id="recipe_001", taste=5, convenience=4, comment="Excellent!"),
                    Rating(user_id="user_2", recipe_id="recipe_001", taste=4, convenience=5, comment="Great recipe"),
                ]
            },
            "filter": {"average_taste_rating_gte": 4.0},
            "should_match": True,
            "description": "Recipe with average taste rating 4.5 should match gte filter of 4.0"
        },
        {
            "scenario_id": "high_convenience_rating",
            "recipe_kwargs": {
                "name": "Convenient Recipe",
                "ratings": [
                    Rating(user_id="user_1", recipe_id="recipe_002", taste=3, convenience=5, comment="Easy to make"),
                    Rating(user_id="user_2", recipe_id="recipe_002", taste=4, convenience=5, comment="Quick recipe"),
                ]
            },
            "filter": {"average_convenience_rating_gte": 4.5},
            "should_match": True,
            "description": "Recipe with average convenience rating 5.0 should match gte filter of 4.5"
        },
        {
            "scenario_id": "no_ratings",
            "recipe_kwargs": {
                "name": "Unrated Recipe",
                "ratings": []
            },
            "filter": {"average_taste_rating_gte": 3.0},
            "should_match": False,
            "description": "Recipe with no ratings should not match rating filter"
        }
    ]


def get_tag_filtering_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing tag filtering.
    
    Returns:
        List of test scenarios with tag filtering expectations
    """
    return [
        {
            "scenario_id": "single_tag_match",
            "recipe_kwargs": {
                "name": "Italian Recipe",
                "tags": {
                    Tag(key="cuisine", value="italian", author_id="author_1", type="recipe")
                }
            },
            "filter": {"tags": [("cuisine", "italian", "author_1")]},
            "should_match": True,
            "description": "Recipe with Italian cuisine tag should match cuisine filter"
        },
        {
            "scenario_id": "multiple_tags_match",
            "recipe_kwargs": {
                "name": "Easy Vegetarian Recipe",
                "tags": {
                    Tag(key="diet", value="vegetarian", author_id="author_1", type="recipe"),
                    Tag(key="difficulty", value="easy", author_id="author_1", type="recipe")
                }
            },
            "filter": {"tags": [("diet", "vegetarian", "author_1"), ("difficulty", "easy", "author_1")]},
            "should_match": True,
            "description": "Recipe with multiple matching tags should match multi-tag filter"
        },
        {
            "scenario_id": "tag_not_exists",
            "recipe_kwargs": {
                "name": "Simple Recipe",
                "tags": {
                    Tag(key="difficulty", value="easy", author_id="author_1", type="recipe")
                }
            },
            "filter": {"tags_not_exists": [("diet", "vegan", "author_1")]},
            "should_match": True,
            "description": "Recipe without vegan tag should match tags_not_exists filter"
        }
    ]


def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """
    Get scenarios for performance testing with dataset expectations.
    
    Returns:
        List of performance test scenarios
    """
    return [
        {
            "scenario_id": "bulk_recipe_creation",
            "dataset_size": 100,
            "expected_time_per_entity": 0.005,  # 5ms per recipe
            "description": "Bulk creation of 100 recipes should complete within 500ms total"
        },
        {
            "scenario_id": "complex_filter_query",
            "dataset_size": 1000,
            "filter": {
                "total_time_gte": 30,
                "total_time_lte": 120,
                "privacy": "public",
                "calories_gte": 200,
                "protein_gte": 15
            },
            "expected_query_time": 1.0,  # 1 second max
            "description": "Complex filter query on 1000 recipes should complete within 1 second"
        },
        {
            "scenario_id": "tag_filtering_performance",
            "dataset_size": 500,
            "filter": {"tags": [("cuisine", "italian", "author_1")]},
            "expected_query_time": 0.5,  # 500ms max
            "description": "Tag filtering on 500 recipes should complete within 500ms"
        }
    ]


# =============================================================================
# SPECIALIZED RECIPE FACTORIES
# =============================================================================

def create_quick_recipe(**kwargs) -> _Recipe:
    """
    Create a quick-cooking recipe (≤20 minutes).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity optimized for quick cooking
    """
    quick_defaults = {
        "name": "Quick Recipe",
        "total_time": 15,
        "instructions": "Quick and easy instructions. Heat, mix, serve.",
        "tags": {
            Tag(key="difficulty", value="easy", author_id="author_1", type="recipe"),
            Tag(key="cooking_method", value="raw", author_id="author_1", type="recipe")
        }
    }
    quick_defaults.update(kwargs)
    return create_recipe(**quick_defaults)


def create_high_protein_recipe(**kwargs) -> _Recipe:
    """
    Create a high-protein recipe (≥25g protein).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity optimized for high protein content
    """
    protein_defaults = {
        "name": "High Protein Recipe",
        "nutri_facts": NutriFacts(
            calories=400.0,
            protein=30.0,  # High protein content
            carbohydrate=15.0,
            total_fat=12.0
        ),
        "ingredients": [
            Ingredient(name="Chicken Breast", unit=MeasureUnit.GRAM, quantity=200.0, position=0, product_id="chicken_123"),
            Ingredient(name="Greek Yogurt", unit=MeasureUnit.GRAM, quantity=100.0, position=1, product_id="yogurt_456"),
        ],
        "tags": {
            Tag(key="diet", value="high-protein", author_id="author_1", type="recipe")
        }
    }
    protein_defaults.update(kwargs)
    return create_recipe(**protein_defaults)


def create_vegetarian_recipe(**kwargs) -> _Recipe:
    """
    Create a vegetarian recipe.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity suitable for vegetarians
    """
    veg_defaults = {
        "name": "Vegetarian Recipe",
        "ingredients": [
            Ingredient(name="Vegetables", unit=MeasureUnit.GRAM, quantity=300.0, position=0, product_id="veggies_123"),
            Ingredient(name="Olive Oil", unit=MeasureUnit.TABLESPOON, quantity=2.0, position=1, product_id="oil_456"),
        ],
        "tags": {
            Tag(key="diet", value="vegetarian", author_id="author_1", type="recipe")
        }
    }
    veg_defaults.update(kwargs)
    return create_recipe(**veg_defaults)


def create_public_recipe(**kwargs) -> _Recipe:
    """
    Create a public recipe for access control testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with public privacy
    """
    public_defaults = {
        "name": "Public Recipe",
        "privacy": Privacy.PUBLIC,
        "description": "This is a public recipe available to all users"
    }
    public_defaults.update(kwargs)
    return create_recipe(**public_defaults)


def create_private_recipe(**kwargs) -> _Recipe:
    """
    Create a private recipe for access control testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with private privacy
    """
    private_defaults = {
        "name": "Private Recipe",
        "privacy": Privacy.PRIVATE,
        "description": "This is a private recipe only visible to the author"
    }
    private_defaults.update(kwargs)
    return create_recipe(**private_defaults)


# =============================================================================
# DATASET CREATION UTILITIES
# =============================================================================

def create_recipes_with_ratings(count: int = 3, ratings_per_recipe: int = 2) -> List[_Recipe]:
    """
    Create a list of recipes with ratings for aggregation testing.
    
    Args:
        count: Number of recipes to create
        ratings_per_recipe: Number of ratings per recipe
        
    Returns:
        List of Recipe entities with ratings
    """
    recipes = []
    for i in range(count):
        ratings = []
        for j in range(ratings_per_recipe):
            rating = create_rating(
                recipe_id=f"recipe_{i+1:03d}",
                user_id=f"user_{j+1}",
                taste=(3 + j) % 6,  # Vary ratings
                convenience=(4 + j) % 6
            )
            ratings.append(rating)
        
        recipe = create_recipe(
            id=f"recipe_{i+1:03d}",
            name=f"Recipe with Ratings {i+1}",
            ratings=ratings
        )
        recipes.append(recipe)
    
    return recipes


def create_test_dataset(recipe_count: int = 100, tags_per_recipe: int = 0) -> Dict[str, Any]:
    """
    Create a comprehensive test dataset for performance and integration testing.
    
    Args:
        recipe_count: Number of recipes to create
        tags_per_recipe: Number of tags per recipe
        
    Returns:
        Dict containing recipes, ingredients, ratings, and metadata
    """
    reset_counters()
    
    recipes = []
    all_ingredients = []
    all_ratings = []
    all_tags = []
    
    for i in range(recipe_count):
        # Create varied recipes
        if i % 4 == 0:
            recipe = create_quick_recipe()
        elif i % 4 == 1:
            recipe = create_high_protein_recipe()
        elif i % 4 == 2:
            recipe = create_vegetarian_recipe()
        else:
            recipe = create_recipe()
        
        # Add tags if requested
        if tags_per_recipe > 0:
            tags = set()
            for j in range(tags_per_recipe):
                tag = create_tag(type="recipe")
                tags.add(tag)
                all_tags.append(tag)
            recipe._tags = tags
        
        # Add ratings (some recipes have ratings, some don't)
        if i % 3 != 0:  # 2/3 of recipes have ratings
            ratings = []
            num_ratings = (i % 3) + 1  # 1-3 ratings per recipe
            for j in range(num_ratings):
                rating = create_rating(recipe_id=recipe.id)
                ratings.append(rating)
                all_ratings.append(rating)
            recipe._ratings = ratings
        
        # Collect ingredients
        all_ingredients.extend(recipe.ingredients)
        recipes.append(recipe)
    
    return {
        "recipes": recipes,
        "ingredients": all_ingredients,
        "ratings": all_ratings,
        "tags": all_tags,
        "metadata": {
            "recipe_count": len(recipes),
            "ingredient_count": len(all_ingredients),
            "rating_count": len(all_ratings),
            "tag_count": len(all_tags),
            "tags_per_recipe": tags_per_recipe
        }
    } 