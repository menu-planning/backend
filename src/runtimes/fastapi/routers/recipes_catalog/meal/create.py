"""FastAPI router for meal create endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import (
    ApiCreateMeal,
)
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/meals")

@router.post("")
async def create_meal(
    request_body: ApiCreateMeal,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Create a new meal.
    
    Args:
        request_body: Meal creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created meal details with meal_id
        
    Raises:
        HTTPException: If user lacks permissions or validation fails
    """   
    cmd = request_body.to_domain(current_user.id)
    
    meal_id = await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Meal created successfully", "meal_id": meal_id},
        status_code=201
    )
