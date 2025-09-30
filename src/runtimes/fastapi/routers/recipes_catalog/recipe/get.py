"""FastAPI router for recipe get endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.core.domain.enums import Permission
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


@router.get("/{recipe_id}")
async def get_recipe(
    recipe_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Get a single recipe by ID.
    
    Args:
        recipe_id: UUID of the recipe to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Recipe details
        
    Raises:
        HTTPException: If recipe not found or invalid ID
    """
    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        try:
            recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundError as err:
            error_message = f"Recipe {recipe_id} not in database"
            raise ValueError(error_message) from err
    
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or current_user.id == recipe.author_id
    ):
        error_message = "User does not have enough privileges to get recipe"
        raise PermissionError(error_message)
    
    api_recipe = ApiRecipe.from_domain(recipe)
    
    response_body = api_recipe.model_dump_json()
    
    return create_success_response(response_body)
