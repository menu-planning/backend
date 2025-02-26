from attrs import asdict

from src.contexts.recipes_catalog.shared.domain.commands import RateRecipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def rate_recipe_handler(cmd: RateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        recipe = await uow.recipes.get(cmd.rating.recipe_id)
        data = asdict(cmd.rating)
        data.pop("recipe_id")
        recipe.rate(**data)
        await uow.recipes.persist(recipe)
        await uow.commit()
