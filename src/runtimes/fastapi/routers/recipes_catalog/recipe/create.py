"""FastAPI router for recipe create endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import (
    ApiCreateRecipe,
)
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/recipes")

@router.post("")
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
    cmd = request_body.to_domain(current_user.id)
    
    recipe_id = await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Recipe created successfully", "recipe_id": recipe_id},
        status_code=201
    )
