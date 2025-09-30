"""FastAPI router for client menu delete endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_delete_menu import (
    ApiDeleteMenu,
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

router = create_router(prefix="/clients", tags=["clients"])


@router.delete("/{client_id}/menus/{menu_id}")
async def delete_menu(
    client_id: str,
    menu_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Delete a menu for a client.
    
    Args:
        client_id: UUID of the client
        menu_id: UUID of the menu to delete
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If client/menu not found, user lacks permissions, or deletion fails
    """
    if not client_id or not menu_id:
        error_message = "Client ID and Menu ID are required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        existing_client = await uow.clients.get(client_id)
    
    if not (
        current_user.has_permission(Permission.MANAGE_CLIENTS)
        or current_user.id == existing_client.author_id
    ):
        error_message = "User does not have enough privileges to delete menu"
        raise PermissionError(error_message)
    
    api_delete_cmd = ApiDeleteMenu(menu_id=menu_id)
    cmd = api_delete_cmd.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {
            "message": "Menu deleted successfully", 
            "client_id": client_id,
            "menu_id": menu_id
        }
    )
