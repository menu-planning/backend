from src.contexts.recipes_catalog.shared.domain.commands.client.create_menu import \
    CreateMenu
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_menu_handler(cmd: CreateMenu, uow: UnitOfWork) -> None:
    async with uow:
        # menu = Menu.create_menu(**asdict(cmd, recurse=False))
        client = await uow.clients.get(cmd.client_id)
        client.create_menu(description=cmd.description,tags=cmd.tags)
        await uow.clients.persist(client)
        await uow.commit()
