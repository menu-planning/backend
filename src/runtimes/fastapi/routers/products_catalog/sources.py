"""FastAPI router for product sources search endpoint."""

from fastapi import Depends, Query
from typing import Annotated, Any, TYPE_CHECKING

from pydantic import TypeAdapter

from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_filter import (
    ApiClassificationFilter,
)
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
from src.logging.logger import get_logger

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork

logger = get_logger(__name__)

SourceListTypeAdapter = TypeAdapter(list[ApiSource])

router = create_router(prefix="/products")


@router.get("/sources")
async def search_product_sources(
    filters: Annotated[ApiClassificationFilter, Query()],
    current_user: Annotated[Any, Depends(get_products_user)],
    bus: MessageBus = Depends(get_products_bus),
) -> Any:
    """Search product sources with pagination and filtering.
    
    Args:
        filters: Source filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Dictionary mapping source IDs to names
    """
    filter_dict = filters.model_dump(exclude_none=True)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result: list = await uow.sources.query(filters=filter_dict)
    
    # Convert domain sources to API format
    api_sources = []
    conversion_errors = 0
    
    for source in result:
        try:
            api_source = ApiSource.from_domain(source)
            api_sources.append(api_source)
        except Exception as e:
            conversion_errors += 1
            logger.warning(
                "Failed to convert source to API format",
                operation="convert_source",
                source_id=getattr(source, "id", "unknown"),
                source_type=type(source).__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            continue
    
    # Return simplified {id: name} mapping
    response_data = {source.id: source.name for source in api_sources}
    
    return create_success_response(response_data)
