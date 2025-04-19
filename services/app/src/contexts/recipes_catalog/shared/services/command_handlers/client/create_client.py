from attrs import asdict

from src.contexts.recipes_catalog.shared.domain.commands.client.create_client import CreateClient
from src.contexts.recipes_catalog.shared.domain.entities.client import Client
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_client_handler(cmd: CreateClient, uow: UnitOfWork) -> None:
    async with uow:
        client = Client.create_client(**asdict(cmd, recurse=False))
        await uow.clients.add(client)
        await uow.commit()
