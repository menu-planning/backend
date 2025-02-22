from src.contexts.recipes_catalog.shared.domain.commands.meal.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_meal(cmd: DeleteMeal, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        meal.delete()
        await uow.meals.persist(meal)
        await uow.commit()
