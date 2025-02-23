from src.contexts.recipes_catalog.shared.domain.commands.menu.delete import DeleteMenu
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_menu(cmd: DeleteMenu, uow: UnitOfWork) -> None:
    async with uow:
        menu = await uow.menus.get(cmd.menu_id)
        menu.delete()
        await uow.menus.persist(menu)
        await uow.commit()
