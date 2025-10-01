"""FastAPI router for client update endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_update_client import (
    ApiUpdateClient,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/clients")

@router.put("/{client_id}")
async def update_client(
    client_id: str,
    request_body: ApiClient,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Update an existing client.
    
    Args:
        client_id: UUID of the client to update
        request_body: Complete client data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Updated client details
        
    Raises:
        HTTPException: If client not found, user lacks permissions, or validation fails
    """
    if not client_id:
        error_message = "Client ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        existing_client = await uow.clients.get(client_id)
    
    if not (
        current_user.has_permission(Permission.MANAGE_CLIENTS)
        or current_user.id == existing_client.author_id
    ):
        error_message = "User does not have enough privileges to update client"
        raise PermissionError(error_message)
    
    existing_api_client = ApiClient.from_domain(existing_client)

    api = ApiUpdateClient.from_api_client(
        api_client=request_body,
        old_api_client=existing_api_client,
    )
    
    cmd = api.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Client updated successfully", "client_id": client_id}
    )
