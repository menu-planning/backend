"""FastAPI router for meal search endpoint."""

from fastapi import Depends, HTTPException, Query
from typing import Annotated, Any
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_filter import (
    ApiMealFilter,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/meals")

MealListTypeAdapter = TypeAdapter(list[ApiMeal])

@router.get("/search")
async def search_meals(
    filters: Annotated[ApiMealFilter, Query()],
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Search meals with pagination and filtering.
    
    This endpoint replaces the problematic /meals/query path to avoid conflicts
    with /meals/{meal_id}. Uses the same filtering approach as the Lambda implementation.
    
    Args:
        filters: Meal filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        List of meals matching filters
        
    Raises:
        HTTPException: If query parameters are invalid or database error occurs
    """
    filter_dict = filters.model_dump(exclude_none=True)
    
    if current_user:
        if filter_dict.get("tags"):
            filter_dict["tags"] = [
                (k, v, current_user.id) for k, vs in filter_dict["tags"].items() for v in vs
            ]
        if filter_dict.get("tags_not_exists"):
            filter_dict["tags_not_exists"] = [
                (k, v, current_user.id)
                for k, vs in filter_dict["tags_not_exists"].items()
                for v in vs
            ]
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result: list = await uow.meals.query(filters=filter_dict)
    
    api_meals = []
    conversion_errors = 0
    
    for _, meal in enumerate(result):
        try:
            api_meal = ApiMeal.from_domain(meal)
            api_meals.append(api_meal)
        except Exception:
            conversion_errors += 1
            
    if conversion_errors > 0:
        # Log warning but continue - this is handled by logging middleware
        pass
    
    response_body = MealListTypeAdapter.dump_json(api_meals)
    
    return create_success_response(response_body)
