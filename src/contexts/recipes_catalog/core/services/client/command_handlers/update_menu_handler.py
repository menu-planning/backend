"""Command handler for updating menu properties."""
from copy import copy
from attr import frozen
from src.contexts.recipes_catalog.core.domain.client.commands.update_menu import (
    UpdateMenu,
)
from src.contexts.recipes_catalog.core.domain.services.sync_menu_and_meal import update_menu_meals_and_manage_related_meals
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import get_logger

logger = get_logger(__name__)

async def update_menu_handler(cmd: UpdateMenu, uow: UnitOfWork) -> None:
    """Apply partial updates to a menu and persist the change."""
    async with uow:
        menu = await uow.menus.get(cmd.menu_id)
        if 'meals' in cmd.updates:
            menu_with_updated_meals = await update_menu_meals_and_manage_related_meals(menu, cmd.updates.pop('meals'), uow)
            menu_with_updated_meals.update_properties(**cmd.updates)
        else:
            menu.update_properties(**cmd.updates)
        await uow.menus.persist(menu)
        await uow.commit()
