import operator

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts._receipt_tracker.shared.adapters.repositories.seller import SellerRepo
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from tests.receipt_tracker.random_refs import random_attr, random_cnpj, random_seller

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def clean_db(session: AsyncSession):
    await session.execute(text("DELETE FROM receipt_tracker.sellers"))
    await session.commit()


async def test_unique_column_works(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    seller = random_seller()
    same_cnpj = seller.replace(name=random_attr("same_cnpj"))
    await repo.add(seller)
    with pytest.raises(IntegrityError):
        await repo.add(same_cnpj)
        await async_pg_session.commit()
        await clean_db(async_pg_session)


async def test_cannot_persist_seller_not_added(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    seller = random_seller()
    with pytest.raises(AssertionError):
        await repo.persist(seller)


async def test_can_list_seller_by_partial_id(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    seller = random_seller()
    await repo.add(seller)
    different_cnpj = seller.replace(cnpj=random_cnpj())
    await repo.add(different_cnpj)
    assert await repo.list_by_partial_id(seller.cnpj[:8]) == [seller]


async def test_can_list_with_empty_filter(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await repo.add(seller_1)
    await repo.add(seller_2)
    result = await repo.query()
    assert seller_1 in result
    assert seller_2 in result


async def test_cannot_use_not_allowed_filter(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    with pytest.raises(BadRequestException):
        await repo.query(filter={"not_allowed": "not_allowed"})


async def test_can_sort(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    a_seller = random_seller()
    a_seller = a_seller.replace(name="A")
    await repo.add(a_seller)
    z_seller = random_seller()
    z_seller = z_seller.replace(name="Z")
    await repo.add(z_seller)
    result = await repo.query(filter={"sort": "-name"})
    ranking = sorted(
        result,
        key=operator.attrgetter(
            "name",
        ),
        reverse=True,
    )
    for a, b in zip(result, ranking):
        print(a.name, b.name)
        assert a == b
    assert result == ranking
    result = await repo.query(filter={"sort": "name"})
    ranking = sorted(
        result,
        key=operator.attrgetter(
            "name",
        ),
    )
    assert set(result) == set(ranking)


async def test_can_skip(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await repo.add(seller_1)
    await repo.add(seller_2)
    all = await repo.query()
    skipped = await repo.query(filter={"skip": 1})
    assert len(list(all)) - len(list(skipped)) == 1


async def test_can_limit(async_pg_session: AsyncSession):
    repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await repo.add(seller_1)
    await repo.add(seller_2)
    result = await repo.query(filter={"limit": 1})
    assert len(list(result)) == 1
