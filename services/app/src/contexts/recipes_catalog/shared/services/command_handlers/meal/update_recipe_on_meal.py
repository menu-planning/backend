from src.contexts.recipes_catalog.shared.domain.commands.meal.update_recipe_on_meal import (
    UpdateRecipeOnMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_recipes_on_meal_handler(
    cmd: UpdateRecipeOnMeal, uow: UnitOfWork
) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        meal.update_recipes(cmd.updates)
        uow.meals.persist(meal)
        await uow.commit()