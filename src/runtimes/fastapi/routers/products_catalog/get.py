"""FastAPI router for product get endpoint."""

from fastapi import Depends
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

router = create_router(prefix="/products", tags=["products"])


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    current_user: Annotated[Any, Depends(get_products_user)],
    bus: MessageBus = Depends(get_products_bus),
) -> Any:
    """Get a single product by ID.
    
    Args:
        product_id: UUID of the product to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Product details
    """
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        product = await uow.products.get(product_id)
    
    api_product = ApiProduct.from_domain(product)
    product_data = api_product.model_dump()
    return create_success_response(product_data)
