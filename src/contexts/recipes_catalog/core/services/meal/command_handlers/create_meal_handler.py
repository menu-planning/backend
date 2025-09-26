"""Command handler for creating a meal aggregate."""

from typing import Callable
from attrs import asdict
from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.services.sync_menu_and_meal import (
    add_newly_created_meal_to_menu,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def create_meal_handler(cmd: CreateMeal, uow_factory: Callable[[],UnitOfWork]) -> None:
    """Create a new `Meal` from command data and persist it."""
    async with uow_factory() as uow:
        if cmd.menu_id:
            assert (
                cmd.menu_meal is not None
            ), "Menu meal is required when menu id is provided"
            menu = await uow.menus.get(cmd.menu_id)
            menu, meal = add_newly_created_meal_to_menu(menu, cmd)
            await uow.meals.add(meal)
            await uow.menus.persist(menu)
            await uow.commit()
        else:
            kwargs = asdict(cmd, recurse=False)
            kwargs.pop("menu_meal")
            meal = Meal.create_meal(**kwargs)
            await uow.meals.add(meal)
            await uow.commit()
