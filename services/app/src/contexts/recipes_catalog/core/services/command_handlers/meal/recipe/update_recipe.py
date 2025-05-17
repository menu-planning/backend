from src.contexts.recipes_catalog.core.domain.commands import UpdateRecipe
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import logger


async def update_recipe_handler(cmd: UpdateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get_meal_by_recipe_id(cmd.recipe_id)
        meal.update_recipes({cmd.recipe_id: cmd.updates})
        await uow.meals.persist(meal)
        await uow.commit()
