from src.contexts.recipes_catalog.core.domain.meal.commands.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def delete_meal_handler(cmd: DeleteMeal, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        meal.delete()
        await uow.meals.persist(meal)
        await uow.commit()
