import datetime
from unittest import mock

import pytest
from aio_pika import RobustChannel

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.recipes_catalog.shared.domain.commands.menu.delete import DeleteMenu
from src.contexts.recipes_catalog.shared.domain.commands.menu.update import UpdateMenu

from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork

from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.recipes_catalog.random_refs import (
    random_meal,
    random_menu,
    random_nutri_facts,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


async def test_deleting_a_menu_remove_menu_id_from_related_meals():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    menu = random_menu()
    meal = random_meal(author_id=menu.author_id)
    meal._menu_id = menu.id
    menu_meal_1: MenuMeal = MenuMeal(
        meal_id=meal.id,
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Lunch",
        nutri_facts=random_nutri_facts(),
        hour=datetime.time(12),
    )
    menu_meal_2: MenuMeal = MenuMeal(
        meal_id="another_meal_id",
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Dinner",
        nutri_facts=random_nutri_facts(),
        hour=datetime.time(19),
    )
    menu._meals = {
        (
            menu_meal_1.week,
            menu_meal_1.weekday,
            menu_meal_1.meal_type,
        ): menu_meal_1,
        (
            menu_meal_2.week,
            menu_meal_2.weekday,
            menu_meal_2.meal_type,
        ): menu_meal_2,
    }
    uow: UnitOfWork
    async with bus_test.uow as uow:
        await uow.menus.add(menu)
        await uow.meals.add(meal)
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert (1, "Monday", "Lunch") in menu.meals
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id
    delete_menu_cmd = DeleteMenu(menu_id=menu.id)
    await bus_test.handle(delete_menu_cmd)
    async with bus_test.uow as uow:
        menus = await uow.menus.query()
        assert len(menus) == 0
        meals = await uow.meals.query()
        assert len(meals) == 0


async def test_adding_a_new_menu_meal_adds_menu_id_to_the_related_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    menu = random_menu()
    meal = random_meal(author_id=menu.author_id)
    menu_meal_1: MenuMeal = MenuMeal(
        meal_id=meal.id,
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Lunch",
        nutri_facts=meal.nutri_facts,
        hour=datetime.time(12),
    )
    uow: UnitOfWork
    async with bus_test.uow as uow:
        await uow.menus.add(menu)
        await uow.meals.add(meal)
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert menu.meals == {}
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id is None
    add_menu_meal_cmd = UpdateMenu(
        menu_id=menu.id,
        updates={"meals": set([menu_meal_1])},
    )
    await bus_test.handle(add_menu_meal_cmd)
    async with bus_test.uow as uow:
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert (1, "Monday", "Lunch") in menu.meals
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id


async def test_removing_a_menu_meal_removes_menu_id_from_the_related_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    menu = random_menu()
    meal = random_meal(author_id=menu.author_id)
    meal._menu_id = menu.id
    menu_meal_1: MenuMeal = MenuMeal(
        meal_id=meal.id,
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Lunch",
        nutri_facts=meal.nutri_facts,
        hour=datetime.time(12),
    )
    menu._meals = {
        (
            menu_meal_1.week,
            menu_meal_1.weekday,
            menu_meal_1.meal_type,
        ): menu_meal_1,
    }
    uow: UnitOfWork
    async with bus_test.uow as uow:
        await uow.menus.add(menu)
        await uow.meals.add(meal)
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert menu.meals == {
            (
                menu_meal_1.week,
                menu_meal_1.weekday,
                menu_meal_1.meal_type,
            ): menu_meal_1,
        }
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id
    remove_menu_meal_cmd = UpdateMenu(
        menu_id=menu.id,
        updates={"meals": set()},
    )
    await bus_test.handle(remove_menu_meal_cmd)
    async with bus_test.uow as uow:
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert menu.meals == {}
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id is None
