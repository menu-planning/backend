"""
TypeAdapter utilities for Lambda endpoint collection responses.

This module provides utility functions for creating TypeAdapters and handling
pagination in Lambda endpoints. Each handler creates its own TypeAdapters
at module level to avoid circular dependencies.

Usage Pattern:
    # In each Lambda handler file (e.g., fetch_recipes.py)
    from pydantic import TypeAdapter
    from src.contexts.shared_kernel.schemas import create_paginated_response
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas import ApiRecipe

    # Create TypeAdapters at module level (once per cold start)
    recipe_list_adapter = TypeAdapter(list[ApiRecipe])
    recipe_collection_adapter = TypeAdapter(CollectionResponse[ApiRecipe])

    # Use in handler
    def lambda_handler(event, context):
        recipes = [ApiRecipe.from_domain(r) for r in domain_recipes]
        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": recipe_list_adapter.dump_json(recipes).decode('utf-8')
        }
"""

from typing import Any, TypeVar

from src.contexts.shared_kernel.adapters.api_schemas.responses.base_response import (
    CollectionResponse,
)

T = TypeVar("T")


def create_paginated_response(
    items: list[T], total_count: int, page_size: int = 50, current_page: int = 1
) -> CollectionResponse[T]:
    """
    Create CollectionResponse with proper pagination metadata.

    This utility function creates the pagination structure used by
    Lambda endpoints that return paginated collections.

    Args:
        items: List of items for current page
        total_count: Total number of items available
        page_size: Number of items per page
        current_page: Current page number (1-based)

    Returns:
        CollectionResponse with pagination metadata

    Example:
        # In Lambda handler
        collection = create_paginated_response(
            items=recipes,
            total_count=150,
            page_size=50,
            current_page=2
        )
        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": recipe_collection_adapter.dump_json(collection).decode('utf-8')
        }
    """
    has_next = (current_page * page_size) < total_count
    has_previous = current_page > 1

    return CollectionResponse[T](
        items=items,
        total_count=total_count,
        page_size=page_size,
        current_page=current_page,
        has_next=has_next,
        has_previous=has_previous,
    )


def extract_pagination_from_query(
    query_params: dict[str, Any], default_page_size: int = 50, max_page_size: int = 200
) -> tuple[int, int]:
    """
    Extract pagination parameters from Lambda event query parameters.

    Args:
        query_params: Query string parameters from Lambda event
        default_page_size: Default page size if not specified
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (current_page, page_size)

    Example:
        # In Lambda handler
        query_params = event.get("queryStringParameters", {}) or {}
        page, page_size = extract_pagination_from_query(query_params)

        # Use for database query
        offset = (page - 1) * page_size
        recipes = await uow.recipes.query(limit=page_size, offset=offset)
    """
    page = max(1, int(query_params.get("page", 1)))
    page_size = min(
        max_page_size, max(1, int(query_params.get("page_size", default_page_size)))
    )
    return page, page_size


def calculate_database_offset(page: int, page_size: int) -> int:
    """
    Calculate database offset from page number.

    Args:
        page: Current page number (1-based)
        page_size: Number of items per page

    Returns:
        Zero-based offset for database queries

    Example:
        page, page_size = extract_pagination_from_query(query_params)
        offset = calculate_database_offset(page, page_size)
        recipes = await uow.recipes.query(limit=page_size, offset=offset)
    """
    return (max(1, page) - 1) * page_size


# Re-export CollectionResponse for convenience
__all__ = [
    "CollectionResponse",
    "calculate_database_offset",
    "create_paginated_response",
    "extract_pagination_from_query",
]
