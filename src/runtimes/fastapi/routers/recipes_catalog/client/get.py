"""FastAPI router for client get endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/clients")

@router.get("/{client_id}")
async def get_client(
    client_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Get a single client by ID.
    
    Args:
        client_id: UUID of the client to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Client details
        
    Raises:
        HTTPException: If client not found or invalid ID
    """
    if not client_id:
        error_message = "Client ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        client = await uow.clients.get(client_id)
    
    if not (
        current_user.has_permission(Permission.MANAGE_CLIENTS)
        or current_user.id == client.author_id
    ):
        error_message = "User does not have enough privileges to get client"
        raise PermissionError(error_message)
    
    api_client = ApiClient.from_domain(client)
    
    response_body = api_client.model_dump_json()
    
    return create_success_response(response_body)
