"""FastAPI router for client search endpoint."""

from fastapi import Depends, HTTPException, Query
from typing import Annotated, Any
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_filter import (
    ApiClientFilter,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/clients")

ClientListTypeAdapter = TypeAdapter(list[ApiClient])

@router.get("/search")
async def search_clients(
    filters: Annotated[ApiClientFilter, Query()],
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Search clients with pagination and filtering.
    
    This endpoint replaces the problematic /clients/query path to avoid conflicts
    with /clients/{client_id}. Uses the same filtering approach as the Lambda implementation.
    
    Args:
        filters: Client filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        List of clients matching filters
        
    Raises:
        HTTPException: If query parameters are invalid or database error occurs
    """
    filter_dict = filters.model_dump(exclude_none=True)
          
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result = await uow.clients.query(filters=filter_dict)
    
    api_clients = [ApiClient.from_domain(client) for client in result]
    
    response_body = ClientListTypeAdapter.dump_json(api_clients)
    
    return create_success_response(response_body)
