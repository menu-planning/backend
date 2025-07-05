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

# Import check_missing_attributes for validation
from tests.utils import check_missing_attributes

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_TAG_COUNTER = 1


def reset_tag_domain_counters() -> None:
    """Reset all counters for test isolation"""
    global _TAG_COUNTER
    _TAG_COUNTER = 1


# =============================================================================
# TAG DATA FACTORIES (DOMAIN)
# =============================================================================

def create_meal_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag kwargs with deterministic values and comprehensive validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # Predefined tag types for realistic test data
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season", "style", "occasion"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"],
        "style": ["comfort-food", "healthy", "fusion", "traditional"],
        "occasion": ["date-night", "family", "quick", "special"]
    }
    
    key = keys[(_TAG_COUNTER - 1) % len(keys)]
    value = values_by_key[key][(_TAG_COUNTER - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", tag_types[(_TAG_COUNTER - 1) % len(tag_types)]),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(Tag, final_kwargs)
    assert not missing, f"Missing attributes for Tag: {missing}"
    
    _TAG_COUNTER += 1
    return final_kwargs


def create_meal_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object with comprehensive validation
    """
    tag_kwargs = create_meal_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)

# =============================================================================
# TAG DATA FACTORIES (DOMAIN)
# =============================================================================

def create_recipe_tag_kwargs(**kwargs) -> Dict[str, Any]:
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
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", "recipe"),  # Always recipe type for recipe tags
    }
    
    _TAG_COUNTER += 1
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
