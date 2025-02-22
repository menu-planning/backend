from copy import deepcopy
from unittest import mock

import pytest
from aio_pika import RobustChannel

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.add_recipe import (
    AddRecipeToMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.copy_existing_recipe import (
    CopyExistingRecipeToMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.copy_meal import CopyMeal
from src.contexts.recipes_catalog.shared.domain.commands.meal.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.remove_recipe import (
    RemoveRecipeFromMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_meal import (
    UpdateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_recipe import (
    UpdateRecipeOnMeal,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.recipes_catalog.random_refs import (
    random_create_meal_cmd_kwargs,
    random_create_recipe_cmd_kwargs,
    random_recipe,
    random_user,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


async def test_can_create_meal_handler():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs()
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert uow.committed


async def test_can_delete_meal_handler():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs()
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert uow.committed
    delete_cmd = DeleteMeal(meal_id=meal.id)
    await bus_test.handle(delete_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 0
        assert uow.committed


async def test_can_add_recipe_to_meal_handler():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    recipe = random_recipe(author_id=meal.author_id, meal_id=meal.id)
    add_recipe_cmd = AddRecipeToMeal(meal_id=meal.id, recipe=recipe)
    await bus_test.handle(add_recipe_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.recipes == [recipe]
        assert uow.committed


async def test_can_copy_and_existing_recipe_to_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    recipe = random_recipe()
    async with bus_test.uow as uow:
        await uow.recipes.add(recipe)
        assert uow.committed
    copy_existing_recipe_cmd = CopyExistingRecipeToMeal(
        meal_id=meal.id, recipe_id=recipe.id
    )
    await bus_test.handle(copy_existing_recipe_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert len(meal.recipes) == 1
        assert meal.recipes[0].meal_id == meal.id != recipe.meal_id
        assert meal.recipes[0].author_id == meal.author_id != recipe.author_id


async def test_can_copy_an_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    copy_cmd = CopyMeal(
        id_of_user_coping_meal="new_user",
        id_of_meal_to_be_copied=meal.id,
        # id_of_target_menu="new_menu",
    )
    await bus_test.handle(copy_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 2
        assert query[0].name == query[1].name
        assert query[0].author_id != query[1].author_id
        assert query[0].id != query[1].id


class TestUpdateMealHandler:
    async def test_happy_update_meal_handler(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        create_kwargs = random_create_meal_cmd_kwargs()
        cmd = CreateMeal(**create_kwargs)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
            assert len(meal) == 0
        await bus_test.handle(cmd)
        async with bus_test.uow as uow:
            query = await uow.meals.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            meal = query[0]
            assert meal is not None
            assert uow.committed
        meal = deepcopy(meal)
        update_kwargs = random_create_meal_cmd_kwargs(
            author_id=cmd.author_id,
            recipes=[random_recipe(author_id=cmd.author_id, meal_id=meal.id)],
        )
        update_kwargs.pop("author_id")
        update_cmd = UpdateMeal(meal_id=meal.id, updates=update_kwargs)
        await bus_test.handle(update_cmd)
        async with bus_test.uow as uow:
            query = await uow.meals.query(
                {"name": update_cmd.updates["name"], "author_id": cmd.author_id}
            )
            updated_meal: Meal = query[0]
            assert meal == updated_meal
            # assert updated_meal.name == update_cmd.updates.get("name")
            for k, v in update_cmd.updates.items():
                if k == "recipes":
                    continue
                else:
                    assert getattr(updated_meal, k) == v
                    assert getattr(meal, k) == create_kwargs[k]
                    if k != "menu_id":
                        assert create_kwargs[k] != v
            for recipe in update_cmd.updates.get("recipes", []):
                assert recipe.name in [r.name for r in updated_meal.recipes]
                assert recipe.author_id == updated_meal.author_id
                for tag in recipe.tags:
                    assert tag in updated_meal.recipes_tags
            for recipe in create_kwargs.get("recipes", []):
                assert recipe.name in [r.name for r in meal.recipes]
                assert recipe.author_id == meal.author_id
                for tag in recipe.tags:
                    assert tag in meal.recipes_tags
                    assert tag not in updated_meal.recipes_tags
                assert recipe.name not in [r.name for r in updated_meal.recipes]
            assert uow.committed

    async def test_canNOT_change_meal_author(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_create_meal_cmd_kwargs()
        cmd = CreateMeal(**kwargs)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
            assert len(meal) == 0
        await bus_test.handle(cmd)
        async with bus_test.uow as uow:
            query = await uow.meals.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            meal = query[0]
            assert meal is not None
            assert uow.committed
        new_author = random_user()
        update_cmd = UpdateMeal(meal_id=meal.id, updates={"author_id": new_author.id})
        with pytest.raises(AttributeError) as exc:
            await bus_test.handle(update_cmd)
        # with pytest.raises(ExceptionGroup) as exc:
        #     await bus_test.handle(update_cmd)
        # assert any(isinstance(e, AttributeError) for e in exc.value.exceptions)
        # assert len(exc.value.exceptions) == 1
        # assert isinstance(exc.value.exceptions[0], AttributeError)


async def test_can_remove_a_recipe_from_a_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    recipe = random_recipe(author_id=meal.author_id, meal_id=meal.id)
    add_recipe_cmd = AddRecipeToMeal(meal_id=meal.id, recipe=recipe)
    await bus_test.handle(add_recipe_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert len(meal.recipes) == 1
        assert meal.recipes == [recipe]
        assert uow.committed
    remove_recipe_cmd = RemoveRecipeFromMeal(meal_id=meal.id, recipe_id=recipe.id)
    await bus_test.handle(remove_recipe_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert len(meal.recipes) == 0
        assert uow.committed


async def test_can_update_a_recipe_on_a_meal():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_meal_cmd_kwargs()
    cmd = CreateMeal(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 3
        assert uow.committed
    recipe = deepcopy(meal.recipes[0])
    update_kwargs = random_create_recipe_cmd_kwargs(author_id=meal.author_id)
    update_kwargs.pop("author_id")
    update_kwargs.pop("meal_id")
    update_cmd = UpdateRecipeOnMeal(
        meal_id=meal.id, recipe_id=recipe.id, updates=update_kwargs
    )
    await bus_test.handle(update_cmd)
    async with bus_test.uow as uow:
        query = await uow.meals.query()
        updated_meal: Meal = query[0]
        for r in updated_meal.recipes:
            if r.id == recipe.id:
                for k, v in update_cmd.updates.items():
                    assert getattr(r, k) == v
