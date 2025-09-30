"""FastAPI router for meal update endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
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

router = create_router(prefix="/meals", tags=["meals"])




@router.put("/{meal_id}")
async def update_meal(
    meal_id: str,
    request_body: ApiMeal,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Update an existing meal.
    
    Args:
        meal_id: UUID of the meal to update
        request_body: Complete meal data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Updated meal details
        
    Raises:
        HTTPException: If meal not found, user lacks permissions, or validation fails
    """
    if not meal_id:
        error_message = "Meal ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        existing_meal = await uow.meals.get(meal_id)
    
    if not (
        current_user.has_permission(Permission.MANAGE_MEALS)
        or current_user.id == existing_meal.author_id
    ):
        error_message = "User does not have enough privileges to update meal"
        raise PermissionError(error_message)
    
    existing_api_meal = ApiMeal.from_domain(existing_meal)
    
    api_update_cmd = ApiUpdateMeal.from_api_meal(
        api_meal=request_body,
        old_api_meal=existing_api_meal,
    )

    cmd = api_update_cmd.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Meal updated successfully"}
    )
