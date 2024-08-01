import random
import traceback

import anyio
import pytest
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from tests.products_catalog.random_refs import (
    DietTypeNames,
    random_attr,
    random_food_product,
)
from tests.products_catalog.utils import insert_diet_type, insert_food_product

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_uow_can_retrieve_a_product_and_update_it(async_pg_session_factory):
    product_id = random_attr("id")
    diet_type_id = random.choice(list(DietTypeNames)).value
    async with UnitOfWork(async_pg_session_factory) as uow:
        await insert_food_product(
            uow.session,
            product_id,
        )
        await insert_diet_type(uow.session, diet_type_id)
        product = await uow.products.get(product_id)
        product.add_diet_types_ids(diet_type_id)
        await uow.products.persist(product)
        product = await uow.products.get(product_id)
        assert product.diet_types_ids == set([diet_type_id])


async def test_rolls_back_uncommitted_work_by_default(async_pg_session_factory):
    product_id = random_attr("id")
    async with async_pg_session_factory() as session:
        await insert_food_product(
            session,
            product_id,
        )
    session: AsyncSession
    async with async_pg_session_factory() as session:
        with pytest.raises(NoResultFound):
            domain_obj = await session.execute(
                text(f"SELECT * FROM products_catalog.products WHERE id=:id"),
                {"id": product_id},
            )
            domain_obj.scalar_one()


async def test_rolls_back_on_error(async_pg_session_factory):
    class MyException(Exception):
        pass

    product_id = random_attr("id")
    with pytest.raises(MyException):
        async with UnitOfWork(async_pg_session_factory) as uow:
            await insert_food_product(
                uow.session,
                product_id,
            )
            raise MyException()
    new_session: AsyncSession
    async with async_pg_session_factory() as new_session:
        with pytest.raises(NoResultFound):
            domain_obj = await new_session.execute(
                text(f"SELECT * FROM products_catalog.products WHERE id=:id"),
                {"id": product_id},
            )
            domain_obj.scalar_one()


async def try_to_add_diet_types(id, exceptions, session_factory, idle_time=0):
    try:
        async with UnitOfWork(session_factory) as uow:
            product = await uow.products.get(id)
            diet_type = random.choice(list(DietTypeNames)).value
            product.add_diet_types_ids(diet_type)
            await uow.products.persist(product)
            await anyio.sleep(idle_time)
            await uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


async def test_concurrent_updates_to_version_are_not_allowed(
    async_pg_session_factory,
):
    product = random_food_product()
    old_version = product.version
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await insert_food_product(
            session,
            id=product.id,
            version=product.version,
        )
        await session.commit()
    exceptions: list[Exception] = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            try_to_add_diet_types, product.id, exceptions, async_pg_session_factory, 1
        )
        tg.start_soon(
            try_to_add_diet_types, product.id, exceptions, async_pg_session_factory
        )

    [[version]] = await session.execute(
        text("SELECT version FROM products_catalog.products WHERE id=:id"),
        {"id": product.id},
    )
    await session.close()
    assert version == old_version + 1
    [exception] = exceptions
    assert "could not serialize access due to concurrent update" in str(exception)
