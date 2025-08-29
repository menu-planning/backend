"""
Products Catalog Core Module

Contains the business logic, repositories, and services for products catalog operations.
"""

# Bootstrap
from src.contexts.products_catalog.core.bootstrap.container import Container

# Domain
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.products_catalog.core.domain.value_objects.product_shopping_data import (
    ProductShoppingData,
)
from src.contexts.products_catalog.core.domain.value_objects.role import Role
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.products_catalog.core.domain.value_objects.user import User

# Services
from src.contexts.products_catalog.core.services.uow import UnitOfWork

__all__ = [
    "Container",
    "IsFoodVotes",
    "Product",
    "ProductShoppingData",
    "Role",
    "Score",
    "UnitOfWork",
    "User",
]
