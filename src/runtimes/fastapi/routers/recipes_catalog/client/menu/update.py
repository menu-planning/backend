"""FastAPI router for client menu update endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_update_menu import (
    ApiUpdateMenu,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import (
    ApiMenu,
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

@router.put("/{client_id}/menus/{menu_id}")
async def update_menu(
    client_id: str,
    menu_id: str,
    request_body: ApiMenu,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Update an existing menu for a client.
    
    Args:
        client_id: UUID of the client
        menu_id: UUID of the menu to update
        request_body: Complete menu data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Updated menu details
        
    Raises:
        HTTPException: If client/menu not found, user lacks permissions, or validation fails
    """
    if not client_id or not menu_id:
        error_message = "Client ID and Menu ID are required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        existing_menu = await uow.menus.get(menu_id)
    
    if not (
        current_user.has_permission(Permission.MANAGE_CLIENTS)
        or current_user.id == existing_menu.author_id
    ):
        error_message = "User does not have enough privileges to update menu"
        raise PermissionError(error_message)

    existing_api_menu = ApiMenu.from_domain(existing_menu)

    api_update_cmd = ApiUpdateMenu.from_api_menu(
        api_menu=request_body,
        old_api_menu=existing_api_menu,
    )
    
    cmd = api_update_cmd.to_domain()
    await bus.handle(cmd)
    
    return create_success_response(
        {
            "message": "Menu updated successfully", 
            "client_id": client_id,
            "menu_id": menu_id
        }
    )
