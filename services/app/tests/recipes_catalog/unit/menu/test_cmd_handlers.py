import datetime
from copy import deepcopy
from unittest import mock

import pytest
from aio_pika import RobustChannel

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.recipes_catalog.shared.domain.commands.client.create_menu import CreateMenu
from src.contexts.recipes_catalog.shared.domain.commands.client.delete_menu import DeleteMenu
from src.contexts.recipes_catalog.shared.domain.commands.client.update_menu import UpdateMenu
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu

from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork

from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.recipes_catalog.random_refs import (
    random_attr,
    random_create_menu_cmd_kwargs,
    random_nutri_facts,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock) # type: ignore
    return fastapi_bootstrap(uow, get_aio_pika_manager()) # type: ignore


async def test_can_create_menu():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_menu_cmd_kwargs()
    cmd = CreateMenu(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow: # type: ignore
        menu = await uow.menus.query()
        assert len(menu) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow: # type: ignore
        query = await uow.menus.query()
        assert len(query) == 1
        menu = query[0]
        assert menu is not None
        assert menu.client_id == cmd.client_id
        assert uow.committed # type: ignore


async def test_can_delete_a_menu():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_menu_cmd_kwargs()
    cmd = CreateMenu(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow: # type: ignore
        menu = await uow.menus.query()
        assert len(menu) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow: # type: ignore
        query = await uow.menus.query()
        assert len(query) == 1
        menu = query[0]
        assert menu is not None
        assert menu.client_id == cmd.client_id
        assert uow.committed # type: ignore
    cmd = DeleteMenu(menu_id=menu.id)
    await bus_test.handle(cmd)
    async with bus_test.uow as uow: # type: ignore
        query = await uow.menus.query()
        assert len(query) == 0
        assert uow.committed # type: ignore


class TestUpdateMenuHandler:
    async def test_happy_update_menu_handler(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        create_kwargs = random_create_menu_cmd_kwargs()
        cmd = CreateMenu(**create_kwargs)
        uow: UnitOfWork
        async with bus_test.uow as uow: # type: ignore
            menu = await uow.menus.query()
            assert len(menu) == 0
        await bus_test.handle(cmd)
        async with bus_test.uow as uow: # type: ignore
            query = await uow.menus.query()
            menu = query[0]
            assert menu is not None
            assert uow.committed # type: ignore
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
        await bus_test.handle(update_cmd)
        async with bus_test.uow as uow: # type: ignore
            query = await uow.menus.query()
            updated_menu: Menu = query[0]
            assert menu == updated_menu
            for k, v in update_cmd.updates.items():
                if k == "meals":
                    assert list(getattr(updated_menu, k).values())[0] == v[0]
                else:
                    assert getattr(updated_menu, k) == v
                    assert getattr(menu, k) == create_kwargs[k] != v
