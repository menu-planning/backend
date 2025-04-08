from src.contexts.recipes_catalog.shared.domain.commands import UpdateRecipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.logging.logger import logger


async def update_recipe_handler(cmd: UpdateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        recipe = await uow.recipes.get(cmd.recipe_id)
        recipe.update_properties(**cmd.updates)
        logger.debug(
            f"recipe ingredients after update: {recipe.ingredients}"
        )
        await uow.recipes.persist(recipe)
        await uow.commit()
