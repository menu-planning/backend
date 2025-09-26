"""Command handler for updating menu properties."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.client.commands.update_menu import (
    UpdateMenu,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def update_menu_handler(cmd: UpdateMenu, uow_factory: Callable[[],UnitOfWork]) -> None:
    """Apply partial updates to a menu and persist the change."""
    async with uow_factory() as uow:
        menu = await uow.menus.get(cmd.menu_id)
        menu.update_properties(**cmd.updates)
        await uow.menus.persist(menu)
        await uow.commit()
