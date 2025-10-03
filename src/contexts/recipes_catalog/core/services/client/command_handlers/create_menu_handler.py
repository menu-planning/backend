"""Command handler for creating a new menu for a client."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.client.commands.create_menu import (
    CreateMenu,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def create_menu_handler(cmd: CreateMenu, uow: UnitOfWork) -> None:
    """Create a menu under the specified client and persist it."""
    async with uow:
        client = await uow.clients.get(cmd.client_id)
        client.create_menu(description=cmd.description, tags=cmd.tags, menu_id=cmd.menu_id)
        await uow.clients.persist(client)
        await uow.commit()
