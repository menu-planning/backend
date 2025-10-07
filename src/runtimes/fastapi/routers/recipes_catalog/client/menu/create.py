"""FastAPI router for client menu create endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_create_menu import (
    ApiCreateMenu,
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

@router.post("/{client_id}/menus")
async def create_menu(
    client_id: str,
    request_body: ApiCreateMenu,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Create a new menu for a client.
    
    Args:
        client_id: UUID of the client
        request_body: Menu creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created menu details with menu_id
        
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
        error_message = "User does not have enough privileges to create menu"
        raise PermissionError(error_message)
    
    cmd = request_body.to_domain(current_user.id)
    
    await bus.handle(cmd)
    
    return create_success_response(
        {
            "message": "Menu created successfully", 
            "client_id": client_id,
            "menu_id": cmd.menu_id
        },
        status_code=201
    )
