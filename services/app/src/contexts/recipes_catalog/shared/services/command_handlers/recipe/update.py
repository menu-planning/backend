from src.contexts.recipes_catalog.shared.domain.commands import UpdateRecipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_recipe(cmd: UpdateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        recipe = await uow.recipes.get(cmd.recipe_id)
        recipe.update_properties(**cmd.updates)
        await uow.recipes.persist(recipe)
        await uow.commit()
