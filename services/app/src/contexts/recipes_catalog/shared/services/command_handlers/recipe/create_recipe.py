from attrs import asdict

from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_recipe_handler(cmd: CreateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        recipe = Recipe.create_recipe(**asdict(cmd, recurse=False))
        await uow.recipes.add(recipe)
        await uow.commit()
        await uow.commit()
