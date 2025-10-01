"""FastAPI router for recipe copy endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_copy_recipe import (
    ApiCopyRecipe,
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

router = create_router(prefix="/recipes")

@router.post("/{recipe_id}/copy")
async def copy_recipe(
    recipe_id: str,
    request_body: ApiCopyRecipe,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Copy an existing recipe.
    
    Args:
        recipe_id: UUID of the recipe to copy
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success message with new recipe_id
        
    Raises:
        HTTPException: If recipe not found, user lacks permissions, or copy fails
    """
    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        existing_recipe = await uow.recipes.get(recipe_id)
    
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or current_user.id == existing_recipe.author_id
    ):
        error_message = "User does not have enough privileges to copy recipe"
        raise PermissionError(error_message)
    
    cmd = request_body.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {
            "message": "Recipe copied successfully"
        },
        status_code=201
    )
