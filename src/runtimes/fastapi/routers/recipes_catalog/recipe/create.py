"""FastAPI router for recipe create endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import (
    ApiCreateRecipe,
)
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/recipes", tags=["recipes"])




@router.post("/")
async def create_recipe(
    request_body: ApiCreateRecipe,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Create a new recipe.
    
    Args:
        request_body: Recipe creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created recipe details with recipe_id
        
    Raises:
        HTTPException: If user lacks permissions or validation fails
    """
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or current_user.id == request_body.author_id
    ):
        error_message = "User does not have enough privileges to create recipe"
        raise PermissionError(error_message)
    
    cmd = request_body.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Recipe created successfully"},
        status_code=201
    )
