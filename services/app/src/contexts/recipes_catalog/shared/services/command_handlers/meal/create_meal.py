from attrs import asdict

from src.contexts.recipes_catalog.shared.domain.commands.meal.create_meal import \
    CreateMeal
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_meal_handler(cmd: CreateMeal, uow: UnitOfWork) -> None:
    async with uow:
        meal = Meal.create_meal(**asdict(cmd, recurse=False))
        await uow.meals.add(meal)
        await uow.commit()
