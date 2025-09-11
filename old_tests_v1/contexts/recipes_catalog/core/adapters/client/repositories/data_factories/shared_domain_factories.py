"""
Data factories for MenuRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different menu types
- ORM equivalents for all domain factory methods

All data follows the exact structure of Menu domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from typing import Any

from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.utils.counter_manager import get_next_tag_id

# =============================================================================
# TAG DATA FACTORIES (SHARED)
# =============================================================================


def create_menu_tag_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create tag kwargs with deterministic values for menu tags.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with tag creation parameters
    """
    # Predefined tag types for realistic menu test data
    keys = ["type", "season", "event", "dietary", "complexity"]
    values_by_key = {
        "type": ["weekly", "special", "holiday", "daily", "custom"],
        "season": ["spring", "summer", "fall", "winter", "year-round"],
        "event": ["wedding", "corporate", "birthday", "conference", "casual"],
        "dietary": ["vegetarian", "vegan", "gluten-free", "keto", "balanced"],
        "complexity": ["simple", "moderate", "complex", "gourmet"],
    }

    tag_counter = get_next_tag_id()
    key = keys[(tag_counter - 1) % len(keys)]
    value = values_by_key[key][(tag_counter - 1) % len(values_by_key[key])]

    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((tag_counter - 1) % 5) + 1}"),
        "type": kwargs.get("type", "menu"),
    }

    return final_kwargs


def create_menu_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        Tag value object
    """
    tag_kwargs = create_menu_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)


# =============================================================================
# TAG DATA FACTORIES (SHARED)
# =============================================================================


def create_client_tag_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create tag kwargs with deterministic values for client tags.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with tag creation parameters
    """
    # Predefined tag types for realistic test data
    keys = ["category", "industry", "size", "region", "priority"]
    values_by_key = {
        "category": ["restaurant", "catering", "hotel", "healthcare", "school"],
        "industry": ["hospitality", "healthcare", "education", "retail", "corporate"],
        "size": ["small", "medium", "large", "enterprise"],
        "region": ["north", "south", "east", "west", "central"],
        "priority": ["high", "medium", "low", "urgent"],
    }

    tag_counter = get_next_tag_id()
    key = keys[(tag_counter - 1) % len(keys)]
    value = values_by_key[key][(tag_counter - 1) % len(values_by_key[key])]

    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((tag_counter - 1) % 5) + 1}"),
        "type": kwargs.get("type", "client"),
    }

    return final_kwargs


def create_client_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        Tag value object
    """
    tag_kwargs = create_client_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)
