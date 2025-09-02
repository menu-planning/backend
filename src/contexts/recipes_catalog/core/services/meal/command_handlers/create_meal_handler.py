"""Command handler for creating a meal aggregate."""
from attrs import asdict
from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def create_meal_handler(cmd: CreateMeal, uow: UnitOfWork) -> None:
    """Create a new `Meal` from command data and persist it."""
    async with uow:
        meal = Meal.create_meal(**asdict(cmd, recurse=False))
        await uow.meals.add(meal)
        await uow.commit()
