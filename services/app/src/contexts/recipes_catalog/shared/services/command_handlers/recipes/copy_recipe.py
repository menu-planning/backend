from src.contexts.recipes_catalog.shared.domain.commands.recipes.copy import CopyRecipe
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def copy_recipe(cmd: CopyRecipe, uow: UnitOfWork) -> None:
    async with uow:
        existing_recipe = await uow.recipes.get(cmd.recipe_id)
        new_recipe = Recipe.copy_recipe(
            recipe=existing_recipe, meal_id=cmd.meal_id, user_id=cmd.user_id
        )
        await uow.recipes.add(new_recipe)
        await uow.commit()
