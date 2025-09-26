"""Command handler for copying an existing meal to a (possibly) new menu."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.meal.commands.copy_meal import CopyMeal
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def copy_meal_handler(cmd: CopyMeal, uow_factory: Callable[[],UnitOfWork]):
    """Handle CopyMeal by creating a new `Meal` copy and persisting it."""
    async with uow_factory() as uow:
        meal_to_be_copied = await uow.meals.get(cmd.meal_id)
        meal = Meal.copy_meal(
            meal=meal_to_be_copied,
            id_of_user_coping_meal=cmd.id_of_user_coping_meal,
            id_of_target_menu=cmd.id_of_target_menu,
        )
        await uow.meals.add(meal)
        await uow.commit()
