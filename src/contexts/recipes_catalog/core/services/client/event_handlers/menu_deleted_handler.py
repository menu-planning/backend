"""Event handler for cascading deletions when a menu is removed."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.client.events.menu_deleted import (
    MenuDeleted,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def delete_related_meals(evt: MenuDeleted, uow_factory: Callable[[],UnitOfWork]):
    """Soft-delete all meals that belong to the deleted menu."""
    async with uow_factory() as uow:
        meals = await uow.meals.query(filters={"menu_id": evt.menu_id})
        for meal in meals:
            meal._discard()
        await uow.meals.persist_all(meals)
        await uow.commit()
