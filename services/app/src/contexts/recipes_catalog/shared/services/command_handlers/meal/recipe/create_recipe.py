from attrs import asdict

from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_recipe_handler(cmd: CreateRecipe, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        meal.create_recipe(**asdict(cmd, recurse=False))
        await uow.meals.persist(meal)
        await uow.commit()
