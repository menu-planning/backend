"""FastAPI router for recipe update endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import (
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
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

@router.put("/{recipe_id}")
async def update_recipe(
    recipe_id: str,
    request_body: ApiRecipe,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Update an existing recipe.
    
    Args:
        recipe_id: UUID of the recipe to update
        request_body: Complete recipe data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Updated recipe details
        
    Raises:
        HTTPException: If recipe not found, user lacks permissions, or validation fails
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
        error_message = "User does not have enough privileges to update recipe"
        raise PermissionError(error_message)
    
    existing_api_recipe = ApiRecipe.from_domain(existing_recipe)

    api_update_cmd = ApiUpdateRecipe.from_api_recipe(
        api_recipe=request_body,
        old_api_recipe=existing_api_recipe,
    )
            
    cmd = api_update_cmd.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Recipe updated successfully"}
    )
