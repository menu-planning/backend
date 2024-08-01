from src.contexts.recipes_catalog.shared.domain.commands import DeleteRecipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_recipe(cmd: DeleteRecipe, uow: UnitOfWork) -> None:
    async with uow:
        recipe = await uow.recipes.get(cmd.id)
        recipe.delete()
        await uow.recipes.persist(recipe)
        await uow.commit()
