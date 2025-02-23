from attrs import asdict

from src.contexts.recipes_catalog.shared.domain.commands.menu.create import CreateMenu
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_menu(cmd: CreateMenu, uow: UnitOfWork) -> None:
    async with uow:
        menu = Menu.create_menu(**asdict(cmd, recurse=False))
        await uow.menus.add(menu)
        await uow.commit()
