"""
Recipes Catalog Core Module

Contains the business logic, repositories, and services for recipes catalog operations.
"""

# Bootstrap
from src.contexts.recipes_catalog.core.bootstrap.container import Container

# Domain
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

__all__ = [
    "Container",
    "Meal",
]
