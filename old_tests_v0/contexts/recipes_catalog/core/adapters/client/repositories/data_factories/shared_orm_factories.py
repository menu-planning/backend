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

from old_tests_v0.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_domain_factories import (
    create_client_tag_kwargs,
    create_menu_tag_kwargs,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)


def create_menu_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        TagSaModel ORM instance
    """
    tag_kwargs = create_menu_tag_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


def create_client_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        TagSaModel ORM instance
    """
    tag_kwargs = create_client_tag_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)
