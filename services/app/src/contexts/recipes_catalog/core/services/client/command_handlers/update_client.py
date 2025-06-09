from src.contexts.recipes_catalog.core.domain.client.commands.update_client import UpdateClient
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def update_client_handler(cmd: UpdateClient, uow: UnitOfWork) -> None:
    async with uow:
        client = await uow.clients.get(cmd.client_id)
        client.update_properties(**cmd.updates)
        await uow.clients.persist(client)
        await uow.commit()
