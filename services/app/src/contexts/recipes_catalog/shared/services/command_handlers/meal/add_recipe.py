from src.contexts.recipes_catalog.shared.domain.commands.meal.add_recipe import (
    AddRecipeToMeal,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def add_recipe_to_meal(cdm: AddRecipeToMeal, uow: UnitOfWork):
    async with uow:
        meal = await uow.meals.get(cdm.meal_id)
        meal.add_recipe(cdm.recipe)
        await uow.meals.persist(meal)
        await uow.commit()
