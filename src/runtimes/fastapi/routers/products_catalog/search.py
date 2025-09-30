"""FastAPI router for product search endpoint."""

from fastapi import Depends, Query
from typing import Annotated, Any
from pydantic import TypeAdapter

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.fastapi.dependencies import get_products_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_products_user
from src.runtimes.fastapi.routers.helpers import (
    create_paginated_response,
    create_router,
)

router = create_router(prefix="/products", tags=["products"])

# Type adapter for JSON serialization
ProductListTypeAdapter = TypeAdapter(list[ApiProduct])


@router.get("/search")
async def search_products(
    filters: Annotated[ApiProductFilter, Query()],
    current_user: Annotated[Any, Depends(get_products_user)],
    bus: MessageBus = Depends(get_products_bus),
) -> Any:
    """Search products with pagination and filtering.
    
    This endpoint replaces the problematic /products/query path to avoid conflicts
    with /products/{product_id}. Uses the same filtering approach as the Lambda implementation.
    
    Args:
        filters: Product filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Paginated list of products matching filters
    """
    filter_dict = filters.model_dump(exclude_none=True)
    
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result: list = await uow.products.query(filters=filter_dict)
    
    # Convert domain products to API format
    api_products = []
    for product in result:
        api_product = ApiProduct.from_domain(product)
        api_products.append(api_product)
    
    # Convert to dict format for response
    products_data = [product.model_dump() for product in api_products]
    
    # Calculate pagination info
    page = (filter_dict.get("skip", 0) // filter_dict.get("limit", 50)) + 1
    limit = filter_dict.get("limit", 50)
    total = len(products_data)
    
    return create_paginated_response(
        data=products_data,
        total=total,
        page=page,
        limit=limit
    )
