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

from typing import Any, Dict

# ORM model imports
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)

# Import check_missing_attributes for validation
from tests.contexts.recipes_catalog.data_factories.shared_domain_factories import (
    create_meal_tag_kwargs,
    create_recipe_tag_kwargs,
)
from tests.utils.utils import check_missing_attributes

# =============================================================================
# TAG DATA FACTORIES (ORM)
# =============================================================================


def create_meal_tag_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create tag ORM kwargs with deterministic values and comprehensive validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with ORM tag creation parameters
    """
    # Use the same logic as domain tags but reuse validation
    tag_kwargs = create_meal_tag_kwargs(**kwargs)

    # ORM models use auto-increment for id, so we prepare kwargs accordingly
    final_kwargs = {
        "key": tag_kwargs["key"],
        "value": tag_kwargs["value"],
        "author_id": tag_kwargs["author_id"],
        "type": tag_kwargs["type"],
    }

    # Allow override of any attribute
    final_kwargs.update(kwargs)

    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(TagSaModel, final_kwargs)
    assert not missing, f"Missing attributes for TagSaModel: {missing}"

    return final_kwargs


def create_meal_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data and validation.

    This factory creates a new tag instance without checking for duplicates.
    Use get_or_create_meal_tag_orm() for database-aware tag creation that
    prevents duplicate key violations.

    Args:
        **kwargs: Override any default values

    Returns:
        TagSaModel ORM instance with comprehensive validation
    """
    tag_kwargs = create_meal_tag_orm_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


async def get_or_create_meal_tag_orm(session, **kwargs) -> TagSaModel:
    """
    Get existing tag or create new one, preventing duplicate key violations.

    This function implements the same logic as TagMapper.map_domain_to_sa to
    ensure tags with identical (key, value, author_id, type) combinations
    are reused rather than creating duplicates.

    Args:
        session: AsyncSession for database operations
        **kwargs: Tag attributes (key, value, author_id, type)

    Returns:
        TagSaModel: Existing tag from database or newly created instance
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    tag_kwargs = create_meal_tag_orm_kwargs(**kwargs)

    # Try to find existing tag with same unique attributes
    stmt = select(TagSaModel).filter_by(
        key=tag_kwargs["key"],
        value=tag_kwargs["value"],
        author_id=tag_kwargs["author_id"],
        type=tag_kwargs["type"],
    )

    result = await session.execute(stmt)
    existing_tag = result.scalar_one_or_none()

    if existing_tag is not None:
        return existing_tag
    else:
        return TagSaModel(**tag_kwargs)


# =============================================================================
# TAG DATA FACTORIES (ORM)
# =============================================================================


def create_recipe_tag_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create tag ORM kwargs with deterministic values for recipes.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with ORM tag creation parameters
    """
    # Use the same logic as domain tags but without incrementing counter twice
    tag_kwargs = create_recipe_tag_kwargs(**kwargs)

    # ORM models use auto-increment for id, so we remove it from kwargs if present
    final_kwargs = {
        "key": kwargs.get("key", tag_kwargs["key"]),
        "value": kwargs.get("value", tag_kwargs["value"]),
        "author_id": kwargs.get("author_id", tag_kwargs["author_id"]),
        "type": kwargs.get("type", tag_kwargs["type"]),
    }
    # Keep the id field for testing purposes - TagSaModel has auto-increment but we can override

    return final_kwargs


def create_recipe_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data for recipes.

    Args:
        **kwargs: Override any default values

    Returns:
        TagSaModel ORM instance
    """
    tag_kwargs = create_recipe_tag_orm_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


async def get_or_create_recipe_tag_orm(session, **kwargs) -> TagSaModel:
    """
    Get existing recipe tag or create new one, preventing duplicate key violations.

    This function implements the same logic as TagMapper.map_domain_to_sa to
    ensure tags with identical (key, value, author_id, type) combinations
    are reused rather than creating duplicates.

    Args:
        session: AsyncSession for database operations
        **kwargs: Tag attributes (key, value, author_id, type)

    Returns:
        TagSaModel: Existing tag from database or newly created instance
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    tag_kwargs = create_recipe_tag_orm_kwargs(**kwargs)

    # Try to find existing tag with same unique attributes
    stmt = select(TagSaModel).filter_by(
        key=tag_kwargs["key"],
        value=tag_kwargs["value"],
        author_id=tag_kwargs["author_id"],
        type=tag_kwargs["type"],
    )

    result = await session.execute(stmt)
    existing_tag = result.scalar_one_or_none()

    if existing_tag is not None:
        return existing_tag
    else:
        return TagSaModel(**tag_kwargs)
