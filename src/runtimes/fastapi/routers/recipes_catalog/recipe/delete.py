"""FastAPI router for recipe delete endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_delete_recipe import (
    ApiDeleteRecipe,
)
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
)
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/recipes", tags=["recipes"])




@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Delete a recipe.
    
    Args:
        recipe_id: UUID of the recipe to delete
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If recipe not found, user lacks permissions, or deletion fails
    """
    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        try:
            existing_recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundError as err:
            error_message = f"Recipe {recipe_id} not found"
            raise ValueError(error_message) from err
    
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or current_user.id == existing_recipe.author_id
    ):
        error_message = "User does not have enough privileges to delete recipe"
        raise PermissionError(error_message)
    
    api_delete_cmd = ApiDeleteRecipe(recipe_id=recipe_id)
    cmd = api_delete_cmd.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Recipe deleted successfully"}
    )
