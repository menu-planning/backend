import datetime
from copy import deepcopy
import pytest

from src.contexts.recipes_catalog.core.domain.commands.client.create_menu import CreateMenu
from src.contexts.recipes_catalog.core.domain.commands.client.delete_menu import DeleteMenu
from src.contexts.recipes_catalog.core.domain.commands.client.update_menu import UpdateMenu
from src.contexts.recipes_catalog.core.domain.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.core.services.command_handlers.client.create_menu import create_menu_handler
from src.contexts.recipes_catalog.core.services.command_handlers.client.delete_menu import delete_menu_handler
from src.contexts.recipes_catalog.core.services.command_handlers.client.update_menu import update_menu_handler
from tests.recipes_catalog.random_refs import (
    random_attr,
    random_create_menu_cmd_kwargs,
    random_nutri_facts,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


async def test_can_create_menu():
    uow = FakeUnitOfWork()
    kwargs = random_create_menu_cmd_kwargs()
    cmd = CreateMenu(**kwargs)
    
    async with uow:
        menu = await uow.menus.query()
        assert len(menu) == 0
    
    await create_menu_handler(cmd, uow)
    
    async with uow:
        query = await uow.menus.query()
        assert len(query) == 1
        menu = query[0]
        assert menu is not None
        assert menu.client_id == cmd.client_id
        assert uow.committed


async def test_can_delete_a_menu():
    uow = FakeUnitOfWork()
    kwargs = random_create_menu_cmd_kwargs()
    cmd = CreateMenu(**kwargs)
    
    async with uow:
        menu = await uow.menus.query()
        assert len(menu) == 0
    
    await create_menu_handler(cmd, uow)
    
    async with uow:
        query = await uow.menus.query()
        assert len(query) == 1
        menu = query[0]
        assert menu is not None
        assert menu.client_id == cmd.client_id
        assert uow.committed
    
    delete_cmd = DeleteMenu(menu_id=menu.id)
    await delete_menu_handler(delete_cmd, uow)
    
    async with uow:
        query = await uow.menus.query()
        assert len(query) == 0
        assert uow.committed


class TestUpdateMenuHandler:
    async def test_happy_update_menu_handler(self):
        uow = FakeUnitOfWork()
        create_kwargs = random_create_menu_cmd_kwargs()
        cmd = CreateMenu(**create_kwargs)
        
        async with uow:
            menu = await uow.menus.query()
            assert len(menu) == 0
        
        await create_menu_handler(cmd, uow)
        
        async with uow:
            query = await uow.menus.query()
            menu = query[0]
            assert menu is not None
            assert uow.committed
        
        menu = deepcopy(menu)
        update_kwargs = random_create_menu_cmd_kwargs(author_id=menu.author_id)
        update_kwargs.pop("author_id")
        update_kwargs.pop("client_id")
        update_kwargs["meals"] = [
            MenuMeal(
                meal_id=random_attr("meal_id"),
                meal_name=random_attr("meal_name"),
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                nutri_facts=random_nutri_facts(),
                hour=datetime.time(12),
            )
        ]
        update_cmd = UpdateMenu(menu_id=menu.id, updates=update_kwargs)
        await update_menu_handler(update_cmd, uow)
        
        async with uow:
            query = await uow.menus.query()
            updated_menu: Menu = query[0]
            assert menu == updated_menu
            for k, v in update_cmd.updates.items():
                if k == "meals":
                    assert list(getattr(updated_menu, k).values())[0] == v[0]
                else:
                    assert getattr(updated_menu, k) == v
                    assert getattr(menu, k) == create_kwargs[k] != v
