"""
Test utilities for Recipe equality testing and validation.
"""

import functools
from typing import Any
from uuid import uuid5, NAMESPACE_DNS

from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe


def assert_recipes_equal(recipe1: _Recipe, recipe2: _Recipe, message: str | None = None) -> None:
    """
    Assert that two recipes are equal with detailed error reporting.
    
    Args:
        recipe1: First recipe to compare
        recipe2: Second recipe to compare
        message: Optional custom error message
        
    Raises:
        AssertionError: If recipes are not equal
    """
    if recipe1 != recipe2:
        raise AssertionError(message)
    
    # Generate detailed error message showing differences
    differences = find_recipe_differences(recipe1, recipe2)
    error_msg = f"Recipes are not equal. Differences found:\n"
    for diff in differences:
        error_msg += f"  - {diff}\n"
    
    if message:
        error_msg = f"{message}\n{error_msg}"
    
    raise AssertionError(error_msg)


def find_recipe_differences(recipe1: _Recipe, recipe2: _Recipe) -> list[str]:
    """
    Find all differences between two recipes.
    
    Args:
        recipe1: First recipe to compare
        recipe2: Second recipe to compare
        
    Returns:
        List[str]: List of difference descriptions
    """
    differences = []
    
    # Get clean __dict__ copies without cache-related attributes
    dict1 = _get_clean_dict(recipe1)
    dict2 = _get_clean_dict(recipe2)
    
    # Compare non-cached attributes from __dict__
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        if key not in dict1:
            differences.append(f"Attribute '{key}' missing in recipe1")
        elif key not in dict2:
            differences.append(f"Attribute '{key}' missing in recipe2")
        elif dict1[key] != dict2[key]:
            differences.append(f"Attribute '{key}': {dict1[key]} != {dict2[key]}")
    
    # Compare cached properties by accessing them (this ensures consistent computation)
    cached_properties = _get_cached_properties(recipe1)
    
    for prop_name in cached_properties:
        try:
            val1 = getattr(recipe1, prop_name)
            val2 = getattr(recipe2, prop_name)
            if val1 != val2:
                differences.append(f"Cached property '{prop_name}': {val1} != {val2}")
        except (AttributeError, Exception) as e:
            differences.append(f"Error comparing cached property '{prop_name}': {e}")
    
    return differences


def _get_clean_dict(recipe: _Recipe) -> dict:
    """
    Get recipe __dict__ without cache-related attributes.
    
    This function dynamically removes all cached property values and cache metadata
    from the instance __dict__ to avoid flaky comparisons.
    """
    dict_copy = recipe.__dict__.copy()
    
    # Remove Entity cache metadata attributes
    cache_metadata_attrs = [
        '_Entity__computed_caches',
        '_class_cached_properties', 
        '_computed_caches',
    ]
    
    for attr in cache_metadata_attrs:
        dict_copy.pop(attr, None)
    
    # Dynamically remove cached property values that might be in __dict__
    cached_properties = _get_cached_properties(recipe)
    for prop_name in cached_properties:
        dict_copy.pop(prop_name, None)
    
    return dict_copy


def _get_cached_properties(recipe: _Recipe) -> frozenset[str]:
    """
    Dynamically detect cached properties from the Recipe class.
    
    Uses the same logic as Entity._is_cached_property() to detect cached properties.
    """
    # First try to get from class attribute (most efficient)
    class_cached = getattr(recipe.__class__, '_class_cached_properties', None)
    if class_cached:
        return class_cached
    
    # Fallback: manually detect cached properties using reflection
    cached_properties = set()
    
    # Check all attributes in the class hierarchy
    for cls in recipe.__class__.__mro__:
        for name, attr in cls.__dict__.items():
            if _is_cached_property(attr):
                cached_properties.add(name)
    
    return frozenset(cached_properties)


def _is_cached_property(attr: Any) -> bool:
    """
    Detect if an attribute is a cached property or similar caching descriptor.
    
    This reuses the same logic as Entity._is_cached_property() for consistency.
    """
    # functools.cached_property (Python 3.8+)
    if hasattr(functools, 'cached_property') and isinstance(attr, functools.cached_property):
        return True
    
    # Custom cached_property implementations often have these characteristics
    if (hasattr(attr, '__get__') and 
        hasattr(attr, '__set_name__') and 
        hasattr(attr, 'func')):
        return True
        
    # lru_cache decorated methods (for backward compatibility during transition)
    if hasattr(attr, '__wrapped__') and hasattr(attr, 'cache_info'):
        return True
        
    return False

# =============================================================================
# DETERMINISTIC ID GENERATION
# =============================================================================

def generate_deterministic_id(seed: str) -> str:
    """
    Generate a deterministic UUID4 string based on a seed value.
    
    This function ensures that the same seed value always produces the same UUID string,
    which is essential for consistent test behavior and reproducible test data.
    
    Args:
        seed: A string seed value used to generate the deterministic UUID
        
    Returns:
        A UUID4-formatted string that is deterministic based on the seed
        
    Example:
        >>> id1 = generate_id("test-seed-123")
        >>> id2 = generate_id("test-seed-123")
        >>> id1 == id2  # True - same seed produces same ID
        >>> 
        >>> id3 = generate_id("different-seed")
        >>> id1 == id3  # False - different seeds produce different IDs
    """
    # Use uuid5 with DNS namespace for deterministic UUID generation
    # This ensures the same seed always produces the same UUID
    deterministic_uuid = uuid5(NAMESPACE_DNS, f"recipe-factory-{seed}")
    return str(deterministic_uuid)