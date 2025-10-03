"""Command handler for deleting a client aggregate."""
from typing import Callable
from src.contexts.recipes_catalog.core.domain.client.commands.delete_client import (
    DeleteClient,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def delete_client_handler(cmd: DeleteClient, uow: UnitOfWork) -> None:
    """Soft-delete the client and persist the change."""
    async with uow:
        client = await uow.clients.get(cmd.client_id)
        client.delete()
        await uow.clients.persist(client)
        await uow.commit()
