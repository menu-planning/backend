from src.contexts.recipes_catalog.core.domain.commands.client.update_menu import UpdateMenu
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def update_menu_handler(cmd: UpdateMenu, uow: UnitOfWork) -> None:
    async with uow:
        menu = await uow.menus.get(cmd.menu_id)
        menu.update_properties(**cmd.updates)
        await uow.menus.persist(menu)
        await uow.commit()
