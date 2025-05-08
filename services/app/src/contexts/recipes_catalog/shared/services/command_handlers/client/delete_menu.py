from src.contexts.recipes_catalog.shared.domain.commands.client.delete_menu import DeleteMenu
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_menu_handler(cmd: DeleteMenu, uow: UnitOfWork) -> None:
    async with uow:
        client = await uow.clients.get(cmd.client_id)
        for menu in client.menus:
            if menu.id == cmd.menu_id:
                client.delete_menu(menu)
                break
        await uow.clients.persist(client)
        await uow.commit()
