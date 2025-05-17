import datetime
from unittest import mock

import pytest
from aio_pika import RobustChannel

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.recipes_catalog.core.domain.commands.meal.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.core.domain.commands.meal.update_meal import (
    UpdateMeal,
)

from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork

from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.recipes_catalog.random_refs import (
    random_create_meal_classmethod_kwargs,
    random_meal,
    random_menu,
    random_nutri_facts,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock) # type: ignore
    return fastapi_bootstrap(uow, get_aio_pika_manager()) # type: ignore


async def test_deleting_a_meal_remove_meals_from_menu():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    menu = random_menu()
    meal = random_meal(author_id=menu.author_id)
    meal._menu_id = menu.id
    meal_to_be_deleted: MenuMeal = MenuMeal(
        meal_id=meal.id,
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Lunch",
        nutri_facts=random_nutri_facts(),
        hour=datetime.time(12),
    )
    meal_NOT_to_be_deleted: MenuMeal = MenuMeal(
        meal_id="another_meal_id",
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Dinner",
        nutri_facts=random_nutri_facts(),
        hour=datetime.time(19),
    )
    menu._meals = {
        meal_to_be_deleted,
        meal_NOT_to_be_deleted,
    }
    uow: UnitOfWork
    async with bus_test.uow as uow: # type: ignore
        await uow.menus.add(menu)
        await uow.meals.add(meal)
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert (1, "Monday", "Lunch") in menu.meals
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id
    delete_meal_cmd = DeleteMeal(meal_id=meal.id)
    await bus_test.handle(delete_meal_cmd)
    async with bus_test.uow as uow: # type: ignore
        query = await uow.meals.query()
        assert len(query) == 0
        query = await uow.menus.query()
        assert len(query) == 1
        menu = query[0]
        assert menu is not None
        assert menu.meals == {
            (
                meal_NOT_to_be_deleted.week,
                meal_NOT_to_be_deleted.weekday,
                meal_NOT_to_be_deleted.meal_type,
            ): meal_NOT_to_be_deleted,
        }


async def test_menu_gets_updated_after_change_in_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    menu = random_menu()
    meal = random_meal(author_id=menu.author_id)
    meal._menu_id = menu.id
    meal_to_be_updated: MenuMeal = MenuMeal(
        meal_id=meal.id,
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Lunch",
        nutri_facts=meal.nutri_facts,
        hour=datetime.time(12),
    )
    meal_NOT_to_be_updated: MenuMeal = MenuMeal(
        meal_id="another_meal_id",
        meal_name=meal.name,
        week=1,
        weekday="Monday",
        meal_type="Dinner",
        nutri_facts=random_nutri_facts(),
        hour=datetime.time(19),
    )
    menu._meals = {
        meal_to_be_updated,
        meal_NOT_to_be_updated,
    }
    uow: UnitOfWork
    async with bus_test.uow as uow: # type: ignore
        await uow.menus.add(menu)
        await uow.meals.add(meal)
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert (1, "Monday", "Lunch") in menu.meals
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id
    update_meal_kwargs = random_create_meal_classmethod_kwargs(
        author_id=menu.author_id, menu_id=menu.id
    )
    for recipe in update_meal_kwargs["recipes"]:
        recipe.meal_id = meal.id
    update_meal_kwargs.pop("menu_id")
    update_meal_kwargs.pop("author_id")
    update_meal_cmd = UpdateMeal(meal_id=meal.id, updates=update_meal_kwargs)
    await bus_test.handle(update_meal_cmd)
    async with bus_test.uow as uow: # type: ignore
        query = await uow.meals.query()
        assert len(query) == 1
        query = await uow.menus.query()
        assert len(query) == 1
        menu = query[0]
        assert menu is not None
        nutri_facts = NutriFacts()
        for recipe in update_meal_kwargs["recipes"]:
            nutri_facts += recipe.nutri_facts
        assert menu.meals == {
            (
                meal_NOT_to_be_updated.week,
                meal_NOT_to_be_updated.weekday,
                meal_NOT_to_be_updated.meal_type,
            ): meal_NOT_to_be_updated,
            (
                meal_to_be_updated.week,
                meal_to_be_updated.weekday,
                meal_to_be_updated.meal_type,
            ): MenuMeal(
                meal_id=meal.id,
                meal_name=update_meal_kwargs["name"],
                week=meal_to_be_updated.week,
                weekday=meal_to_be_updated.weekday,
                meal_type=meal_to_be_updated.meal_type,
                nutri_facts=nutri_facts,
                hour=meal_to_be_updated.hour,
            ),
        }
