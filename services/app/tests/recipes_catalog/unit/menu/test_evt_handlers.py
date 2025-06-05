import datetime
from unittest import mock

import pytest

from src.contexts.recipes_catalog.core.domain.commands.client.delete_menu import DeleteMenu
from src.contexts.recipes_catalog.core.domain.commands.client.update_menu import UpdateMenu
from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.core.services.command_handlers.client.delete_menu import delete_menu_handler
from src.contexts.recipes_catalog.core.services.command_handlers.client.update_menu import update_menu_handler
from tests.recipes_catalog.random_refs import (
    random_meal,
    random_menu,
    random_nutri_facts,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio

async def test_deleting_a_menu_remove_menu_id_from_related_meals():
    uow = FakeUnitOfWork()
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
        menu_meal_1,
        menu_meal_2,
    }
    async with uow:
        await uow.menus.add(menu)
        await uow.meals.add(meal)
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert (1, "Monday", "Lunch") in menu.meals
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id

    delete_menu_cmd = DeleteMenu(menu_id=menu.id)
    await delete_menu_handler(delete_menu_cmd, uow)

    async with uow:
        menus = await uow.menus.query()
        assert len(menus) == 0
        meals = await uow.meals.query()
        assert len(meals) == 0


async def test_adding_a_new_menu_meal_adds_menu_id_to_the_related_meal():
    uow = FakeUnitOfWork()
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
    async with uow:
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
    await update_menu_handler(add_menu_meal_cmd, uow)

    async with uow:
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert (1, "Monday", "Lunch") in menu.meals
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id == menu.id


async def test_removing_a_menu_meal_removes_menu_id_from_the_related_meal():
    uow = FakeUnitOfWork()
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
        menu_meal_1,
    }
    async with uow:
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
    await update_menu_handler(remove_menu_meal_cmd, uow)

    async with uow:
        menu = await uow.menus.get(menu.id)
        assert menu is not None
        assert menu.meals == {}
        meal = await uow.meals.get(meal.id)
        assert meal is not None
        assert meal.menu_id is None
