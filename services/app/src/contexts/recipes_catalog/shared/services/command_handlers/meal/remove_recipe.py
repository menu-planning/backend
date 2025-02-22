from src.contexts.recipes_catalog.shared.domain.commands.meal.remove_recipe import (
    RemoveRecipeFromMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def remove_recipe_from_meal(cmd: RemoveRecipeFromMeal, uow: UnitOfWork):
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        meal.remove_recipe(cmd.recipe_id)
        await uow.meals.persist(meal)
        await uow.commit()
