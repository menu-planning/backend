from src.contexts.recipes_catalog.shared.domain.events import MealPlanningCreated
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def meal_planning_created_place_holder(
    evt: MealPlanningCreated, uow: UnitOfWork
) -> None:
    pass
