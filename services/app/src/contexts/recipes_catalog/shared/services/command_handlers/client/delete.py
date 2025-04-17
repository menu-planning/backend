from src.contexts.recipes_catalog.shared.domain.commands.client.delete_client import DeleteClient
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_client_handler(cmd: DeleteClient, uow: UnitOfWork) -> None:
    async with uow:
        client = await uow.clients.get(cmd.client_id)
        client.delete()
        await uow.clients.persist(client)
        await uow.commit()
