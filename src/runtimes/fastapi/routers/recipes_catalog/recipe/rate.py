"""FastAPI router for recipe rate endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_rate_recipe import (
    ApiRateRecipe,
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

router = create_router(prefix="/recipes", tags=["recipes"])


@router.post("/{recipe_id}/rate")
async def rate_recipe(
    recipe_id: str,
    request_body: ApiRateRecipe,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Rate a recipe.
    
    Args:
        recipe_id: UUID of the recipe to rate
        request_body: Rating data (rating value and optional comment)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If recipe not found, invalid rating, or rating fails
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
        error_message = "User does not have enough privileges to rate recipe"
        raise PermissionError(error_message)
    
    cmd = request_body.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {
            "message": "Recipe rated successfully"
        }
    )
