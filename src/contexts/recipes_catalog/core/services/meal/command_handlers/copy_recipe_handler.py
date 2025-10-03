"""Command handler for copying a recipe between meals."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.meal.commands.copy_recipe import (
    CopyRecipe,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def copy_recipe_handler(cmd: CopyRecipe, uow: UnitOfWork) -> None:
    """Copy recipe identified by `cmd.recipe_id` into target `cmd.meal_id`."""
    async with uow:
        source_meal = await uow.meals.get_meal_by_recipe_id(cmd.recipe_id)
        target_meal = await uow.meals.get(cmd.meal_id)
        recipe_to_be_copied = source_meal.get_recipe_by_id(cmd.recipe_id)
        assert recipe_to_be_copied is not None, (
            f"meal {source_meal.id} should have recipe {cmd.recipe_id}"
        )
        target_meal.copy_recipe(recipe_to_be_copied)
        await uow.meals.persist(target_meal)
        await uow.commit()
