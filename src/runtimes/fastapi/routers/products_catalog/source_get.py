"""FastAPI router for product source get endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import (
    ApiSource,
)
from src.contexts.products_catalog.fastapi.dependencies import get_products_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_products_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/products", tags=["products"])


@router.get("/sources/{source_id}")
async def get_product_source(
    source_id: str,
    current_user: Annotated[Any, Depends(get_products_user)],
    bus: MessageBus = Depends(get_products_bus),
) -> Any:
    """Get a single product source by ID.
    
    Args:
        source_id: UUID of the source to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Source details as {id: name} mapping
    """
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        source = await uow.sources.get(source_id)
    
    api_source = ApiSource.from_domain(source)
    response_data = {api_source.id: api_source.name}
    return create_success_response(response_data)
