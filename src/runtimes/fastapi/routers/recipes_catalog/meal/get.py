"""FastAPI router for meal get endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
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

router = create_router(prefix="/meals", tags=["meals"])




@router.get("/{meal_id}")
async def get_meal(
    meal_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Get a single meal by ID.
    
    Args:
        meal_id: UUID of the meal to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Meal details
        
    Raises:
        HTTPException: If meal not found or invalid ID
    """
    if not meal_id:
        error_message = "Meal ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        try:
            meal = await uow.meals.get(meal_id)
        except EntityNotFoundError as err:
            error_message = f"Meal {meal_id} not found"
            raise ValueError(error_message) from err
    
    if not (
        current_user.has_permission(Permission.MANAGE_MEALS)
        or current_user.id == meal.author_id
    ):
        error_message = "User does not have enough privileges to get meal"
        raise PermissionError(error_message)
    
    api_meal = ApiMeal.from_domain(meal)
    
    response_body = api_meal.model_dump_json()
    
    return create_success_response(response_body)
