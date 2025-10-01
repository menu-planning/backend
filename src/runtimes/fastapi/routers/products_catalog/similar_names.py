"""FastAPI router for product similar names search endpoint."""

from fastapi import Depends, Query
from typing import Annotated, Any

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.fastapi.dependencies import get_products_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_products_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/products")


@router.get("/search/similar-names")
async def search_similar_names(
    current_user: Annotated[Any, Depends(get_products_user)],
    bus: MessageBus = Depends(get_products_bus),
    name: str = Query(..., description="Product name to search for"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
) -> Any:
    """Search for products with similar names.
    
    Args:
        name: Product name to search for
        limit: Maximum number of results to return
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        List of products with similar names
    """
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result: list = await uow.products.list_top_similar_names(name)
    
    # Convert domain products to API format
    api_products = []
    for product in result:
        api_product = ApiProduct.from_domain(product)
        api_products.append(api_product)
    
    # Convert to dict format for response
    results_data = [product.model_dump() for product in api_products]
    return create_success_response(results_data)
