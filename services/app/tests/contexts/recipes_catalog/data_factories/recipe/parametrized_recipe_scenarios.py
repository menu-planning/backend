# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

from typing import Any

from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


def get_recipe_filter_scenarios() -> list[dict[str, Any]]:
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


def get_ingredient_relationship_scenarios() -> list[dict[str, Any]]:
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


def get_rating_aggregation_scenarios() -> list[dict[str, Any]]:
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


def get_tag_filtering_scenarios() -> list[dict[str, Any]]:
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


def get_performance_test_scenarios() -> list[dict[str, Any]]:
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


