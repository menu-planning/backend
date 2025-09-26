"""Command handler for updating recipe properties."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe import (
    UpdateRecipe,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def update_recipe_handler(cmd: UpdateRecipe, uow_factory: Callable[[],UnitOfWork]) -> None:
    """Apply partial updates to a recipe via its owning meal and persist."""
    async with uow_factory() as uow:
        meal = await uow.meals.get_meal_by_recipe_id(cmd.recipe_id)
        meal.update_recipes({cmd.recipe_id: cmd.updates})
        await uow.meals.persist(meal)
        await uow.commit()
