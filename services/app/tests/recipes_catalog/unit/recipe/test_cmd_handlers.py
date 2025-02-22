from copy import deepcopy
from unittest import mock

import pytest
from aio_pika import RobustChannel

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.recipes_catalog.shared.domain.commands import (
    CreateRecipe,
    DeleteRecipe,
    RateRecipe,
    UpdateRecipe,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.recipes_catalog.random_refs import (
    random_create_recipe_cmd_kwargs,
    random_rating,
    random_user,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


async def test_create_recipe_handler():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_recipe_cmd_kwargs()
    cmd = CreateRecipe(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.recipes.query()
        recipe = query[0]
        assert recipe is not None
        assert uow.committed


async def test_delete_recipe_handler():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_recipe_cmd_kwargs()
    cmd = CreateRecipe(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        recipe = query[0]
        assert recipe is not None
        assert uow.committed
    delete_cmd = DeleteRecipe(recipe_id=recipe.id)
    await bus_test.handle(delete_cmd)
    async with bus_test.uow as uow:
        query = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(query) == 0
        assert uow.committed


async def test_rate_a_recipe_handler():
    mock_channel = mock.Mock(spec=RobustChannel)
    aio_pika_manager_mock = mock.AsyncMock(spec=AIOPikaManager, channel=mock_channel)
    bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
    kwargs = random_create_recipe_cmd_kwargs()
    cmd = CreateRecipe(**kwargs)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 0
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        query = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        recipe = query[0]
        assert recipe is not None
        assert uow.committed
    rating = random_rating(recipe_id=recipe.id)
    rate_cmd = RateRecipe(rating=rating)
    await bus_test.handle(rate_cmd)
    async with bus_test.uow as uow:
        query = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        recipe = query[0]
        assert recipe is not None
        assert recipe.ratings[0] == rate_cmd.rating
        assert uow.committed


class TestUpdateRecipeHandler:
    async def test_happy_update_recipe_handler(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        create_kwargs = random_create_recipe_cmd_kwargs()
        cmd = CreateRecipe(**create_kwargs)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            recipe = await uow.recipes.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            assert len(recipe) == 0
        await bus_test.handle(cmd)
        async with bus_test.uow as uow:
            query = await uow.recipes.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            recipe = query[0]
            assert recipe is not None
            assert uow.committed
        recipe = deepcopy(recipe)
        update_kwargs = random_create_recipe_cmd_kwargs(author_id=cmd.author_id)
        update_kwargs.pop("author_id")
        update_kwargs.pop("meal_id")
        update_cmd = UpdateRecipe(recipe_id=recipe.id, updates=update_kwargs)
        await bus_test.handle(update_cmd)
        async with bus_test.uow as uow:
            query = await uow.recipes.query(
                {"name": update_cmd.updates["name"], "author_id": cmd.author_id}
            )
            updated_recipe: Recipe = query[0]
            assert recipe == updated_recipe
            assert updated_recipe.name == update_cmd.updates.get("name")
            for k, v in update_cmd.updates.items():
                assert getattr(updated_recipe, k) == v
                assert getattr(recipe, k) == create_kwargs[k]
            assert uow.committed

    async def test_canNOT_change_recipe_author(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_create_recipe_cmd_kwargs()
        cmd = CreateRecipe(**kwargs)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            recipe = await uow.recipes.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            assert len(recipe) == 0
        await bus_test.handle(cmd)
        async with bus_test.uow as uow:
            query = await uow.recipes.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            recipe = query[0]
            assert recipe is not None
            assert uow.committed
        new_author = random_user()
        update_cmd = UpdateRecipe(
            recipe_id=recipe.id, updates={"author_id": new_author.id}
        )
        with pytest.raises(AttributeError) as exc:
            await bus_test.handle(update_cmd)
        # with pytest.raises(ExceptionGroup) as exc:
        #     await bus_test.handle(update_cmd)
        # assert any(isinstance(e, AttributeError) for e in exc.value.exceptions)
        # assert len(exc.value.exceptions) == 1
        # assert isinstance(exc.value.exceptions[0], AttributeError)
