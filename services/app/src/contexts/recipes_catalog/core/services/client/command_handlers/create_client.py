from attrs import asdict

from src.contexts.recipes_catalog.core.domain.client.commands.create_client import CreateClient
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def create_client_handler(cmd: CreateClient, uow: UnitOfWork) -> None:
    async with uow:
        client = Client.create_client(**asdict(cmd, recurse=False))
        await uow.clients.add(client)
        await uow.commit()
