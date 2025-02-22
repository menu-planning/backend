from src.contexts.recipes_catalog.shared.domain.commands.meal.update_recipe import (
    UpdateRecipeOnMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_recipe_on_meal(cmd: UpdateRecipeOnMeal, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        for recipe in meal.recipes:
            if recipe.id == cmd.recipe_id:
                meal.update_recipe(recipe.id, **cmd.updates)
                await uow.meals.persist(meal)
                await uow.commit()
                return
