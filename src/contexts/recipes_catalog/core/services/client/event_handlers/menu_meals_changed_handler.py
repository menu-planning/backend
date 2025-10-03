"""Event handler for syncing menu_id on meals when menu composition changes."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.client.events.menu_meals_changed import (
    MenuMealAddedOrRemoved,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def update_menu_id_on_meals(evt: MenuMealAddedOrRemoved, uow_factory: Callable[[],UnitOfWork]):
    """Update `meal.menu_id` for meals added to/removed from a menu and persist."""
    async with uow_factory() as uow:
        meals = await uow.meals.query(
            filters={"id": list(evt.ids_of_meals_added.union(evt.ids_of_meals_removed))}
        )
        for meal in meals:
            if meal.id in evt.ids_of_meals_added:
                meal._menu_id = evt.menu_id
            if meal.id in evt.ids_of_meals_removed:
                meal._menu_id = None
        await uow.meals.persist_all(meals)
        await uow.commit()
