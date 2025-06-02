from src.contexts.recipes_catalog.core.domain.commands.client.create_menu import \
    CreateMenu
from src.contexts.recipes_catalog.core.domain.entities.menu import Menu
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def create_menu_handler(cmd: CreateMenu, uow: UnitOfWork) -> None:
    async with uow:
        # menu = Menu.create_menu(**asdict(cmd, recurse=False))
        client = await uow.clients.get(cmd.client_id)
        client.create_menu(description=cmd.description, tags=cmd.tags, menu_id=cmd.menu_id)
        await uow.clients.persist(client)
        await uow.commit()
