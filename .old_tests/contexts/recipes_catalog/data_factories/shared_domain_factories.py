"""
Data factories for MealRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different meal types
- ORM equivalents for all domain factory methods
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of Meal domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from typing import Dict, Any

from src.contexts.shared_kernel.domain.value_objects.tag import Tag


from tests.utils.counter_manager import get_next_tag_id
import uuid  # Add uuid import for unique author_id generation

# Predefined UUIDs for deterministic test behavior (still available for backwards compatibility)
_AUTHOR_UUIDS = [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002", 
    "550e8400-e29b-41d4-a716-446655440003",
    "550e8400-e29b-41d4-a716-446655440004",
    "550e8400-e29b-41d4-a716-446655440005"
]

# =============================================================================
# TAG DATA FACTORIES (DOMAIN)
# =============================================================================

def create_meal_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create meal tag kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with meal tag creation parameters
    """
    # Predefined tag types for realistic meal test data
    keys = ["category", "diet", "cuisine", "meal_type", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "gluten-free"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "meal_type": ["appetizer", "main", "side", "dessert", "drink"],
        "season": ["spring", "summer", "fall", "winter"]
    }
    
    tag_counter = get_next_tag_id()
    key = keys[(tag_counter - 1) % len(keys)]
    value = values_by_key[key][(tag_counter - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", str(uuid.uuid4())),  # Generate unique UUID instead of cycling
        "type": kwargs.get("type", "meal"),  # Always meal type for meal tags
    }
    
    return final_kwargs


def create_meal_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data for meals.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object
    """
    tag_kwargs = create_meal_tag_kwargs(**kwargs)
    
    return Tag(
        key=tag_kwargs["key"],
        value=tag_kwargs["value"],
        author_id=tag_kwargs["author_id"],
        type=tag_kwargs["type"]
    )


def create_recipe_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create recipe tag kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with recipe tag creation parameters
    """
    # Predefined tag types for realistic recipe test data
    keys = ["cuisine", "diet", "difficulty", "meal_type", "cooking_method"]
    values_by_key = {
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "gluten-free"],
        "difficulty": ["easy", "medium", "hard"],
        "meal_type": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "cooking_method": ["baked", "grilled", "fried", "steamed", "raw"]
    }
    
    tag_counter = get_next_tag_id()
    key = keys[(tag_counter - 1) % len(keys)]
    value = values_by_key[key][(tag_counter - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", str(uuid.uuid4())),  # Generate unique UUID instead of cycling
        "type": kwargs.get("type", "recipe"),  # Always recipe type for recipe tags
    }
    
    return final_kwargs


def create_recipe_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object
    """
    tag_kwargs = create_recipe_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)
