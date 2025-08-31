from src.contexts.recipes_catalog.core.domain.meal.commands.rate_recipe import (
    RateRecipe,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def rate_recipe_handler(cmd: RateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get_meal_by_recipe_id(cmd.rating.recipe_id)
        meal.rate_recipe(
            recipe_id=cmd.rating.recipe_id,
            user_id=cmd.rating.user_id,
            taste=cmd.rating.taste,
            convenience=cmd.rating.convenience,
            comment=cmd.rating.comment,
        )
        await uow.meals.persist(meal)
        await uow.commit()
