from src.contexts.recipes_catalog.shared.domain.commands.meal.copy_existing_recipe import (
    CopyExistingRecipeToMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def copy_existing_recipe_to_meal(cmd: CopyExistingRecipeToMeal, uow: UnitOfWork):
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        recipe = await uow.recipes.get(cmd.recipe_id)
        meal.copy_recipes([recipe])
        await uow.meals.persist(meal)
        await uow.commit()
