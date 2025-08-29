from src.contexts.recipes_catalog.core.domain.client.commands.delete_menu import (
    DeleteMenu,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def delete_menu_handler(cmd: DeleteMenu, uow: UnitOfWork) -> None:
    async with uow:
        client = await uow.clients.query(filters={"menu_id": cmd.menu_id})
        client = client[0]
        assert client is not None, f"Client with menu_id {cmd.menu_id} not found."
        for menu in client.menus:
            if menu.id == cmd.menu_id:
                client.delete_menu(menu)
                break
        await uow.clients.persist(client)
        await uow.commit()
