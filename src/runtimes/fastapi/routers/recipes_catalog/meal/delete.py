"""FastAPI router for meal delete endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_delete_meal import (
    ApiDeleteMeal,
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


@router.delete("/{meal_id}")
async def delete_meal(
    meal_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Delete a meal.
    
    Args:
        meal_id: UUID of the meal to delete
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If meal not found, user lacks permissions, or deletion fails
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
        error_message = "User does not have enough privileges to delete meal"
        raise PermissionError(error_message)
    
    api_delete_cmd = ApiDeleteMeal(meal_id=meal_id)
    cmd = api_delete_cmd.to_domain()
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Meal deleted successfully"}
    )
