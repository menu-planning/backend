from src.contexts.recipes_catalog.shared.domain.commands.meals.update_meal import (
    UpdateMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_meal(cmd: UpdateMeal, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        meal.update_properties(**cmd.updates)
        await uow.meals.persist(meal)
        await uow.commit()
