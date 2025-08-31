from src.contexts.recipes_catalog.core.domain.meal.commands.delete_recipe import (
    DeleteRecipe,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def delete_recipe_handler(cmd: DeleteRecipe, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get_meal_by_recipe_id(cmd.recipe_id)
        meal.delete_recipe(cmd.recipe_id)
        await uow.meals.persist(meal)
        await uow.commit()
