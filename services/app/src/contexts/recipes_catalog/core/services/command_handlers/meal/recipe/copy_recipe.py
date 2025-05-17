from src.contexts.recipes_catalog.core.domain.commands.recipe.copy import \
    CopyRecipe
from src.contexts.recipes_catalog.core.domain.entities import _Recipe
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def copy_recipe_handler(cmd: CopyRecipe, uow: UnitOfWork) -> None:
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
