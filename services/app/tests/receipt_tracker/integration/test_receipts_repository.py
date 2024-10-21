import operator
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts._receipt_tracker.shared.adapters.repositories.receipt import (
    ReceiptRepo,
)
from src.contexts._receipt_tracker.shared.adapters.repositories.seller import SellerRepo
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from tests.receipt_tracker.random_refs import random_attr, random_receipt, random_seller

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def clean_db(session: AsyncSession):
    await session.execute(text("DELETE FROM receipt_tracker.receipts"))
    await session.execute(text("DELETE FROM receipt_tracker.sellers"))
    await session.commit()


async def test_unique_column_works(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller = random_seller()
    repo = ReceiptRepo(async_pg_session)
    await seller_repo.add(seller)
    receipt = random_receipt(seller_id=seller.cnpj)
    same_cfe_key = Receipt(
        cfe_key=receipt.id,
        house_ids=[random_attr("house_id")],
        state=receipt.state,
        seller_id=receipt.seller_id,
    )
    await repo.add(receipt)
    with pytest.raises(IntegrityError):
        await repo.add(same_cfe_key)
        await async_pg_session.commit()
        await clean_db(async_pg_session)


async def test_cannot_persist_receipt_not_added(async_pg_session: AsyncSession):
    repo = ReceiptRepo(async_pg_session)
    receipt = random_receipt()
    with pytest.raises(AssertionError):
        await repo.persist(receipt)


async def test_can_list_receipt_by_house_id(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await seller_repo.add(seller_1)
    await seller_repo.add(seller_2)
    receipt_repo = ReceiptRepo(async_pg_session)
    receipt_1 = random_receipt(seller_id=seller_1.cnpj)
    await receipt_repo.add(receipt_1)
    receipt_2 = random_receipt(seller_id=seller_2.cnpj)
    await receipt_repo.add(receipt_2)
    # await receipt_repo._session.commit()
    assert await receipt_repo.list_by_house_id(receipt_1.house_ids[0]) == [receipt_1]


async def test_can_list_with_empty_filter(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await seller_repo.add(seller_1)
    await seller_repo.add(seller_2)
    receipt_repo = ReceiptRepo(async_pg_session)
    receipt_1 = random_receipt(seller_id=seller_1.cnpj)
    receipt_2 = random_receipt(seller_id=seller_2.cnpj)
    await receipt_repo.add(receipt_1)
    await receipt_repo.add(receipt_2)
    result = await receipt_repo.query()
    assert receipt_1 in result
    assert receipt_2 in result


async def test_can_list_with_allowed_filter(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller = random_seller()
    await seller_repo.add(seller)
    repo = ReceiptRepo(async_pg_session)
    old_receipt = random_receipt(
        state="SP",
        seller_id=seller.cnpj,
        date=datetime.now()
        - timedelta(
            days=30,
        ),
    )
    new_receipt = random_receipt(
        state="MG",
        seller_id=seller.cnpj,
        date=datetime.now(),
    )
    await repo.add(old_receipt)
    await repo.add(new_receipt)
    exist = await repo.query(
        filter={
            "state": new_receipt.state,
            "seller_id": new_receipt.seller_id,
            "date_gte": new_receipt.date - timedelta(days=1),
        }
    )
    do_not_exist = await repo.query(
        filter={
            "state": old_receipt.state,
            "seller_id": old_receipt.seller_id,
            "date_lte": old_receipt.date - timedelta(days=1),
        }
    )
    assert exist == [new_receipt]
    assert len(list(do_not_exist)) == 0


async def test_can_list_with_negate_filter(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller = random_seller()
    await seller_repo.add(seller)
    repo = ReceiptRepo(async_pg_session)
    old_receipt = random_receipt(
        state="SP",
        seller_id=seller.cnpj,
        date=datetime.now()
        - timedelta(
            days=30,
        ),
    )
    new_receipt = random_receipt(
        state="MG",
        seller_id=seller.cnpj,
        date=datetime.now(),
    )
    await repo.add(old_receipt)
    await repo.add(new_receipt)
    all_receipts = await repo.query()
    negate = await repo.query(
        filter={
            "state_ne": new_receipt.state,
        }
    )
    assert all(i in all_receipts for i in negate)
    assert new_receipt not in negate
    assert new_receipt in all_receipts


async def test_cannot_use_not_allowed_filter(async_pg_session: AsyncSession):
    repo = ReceiptRepo(async_pg_session)
    with pytest.raises(BadRequestException):
        await repo.query(filter={"not_allowed": "not_allowed"})


async def test_can_sort(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller = random_seller()
    await seller_repo.add(seller)
    repo = ReceiptRepo(async_pg_session)
    old_receipt = random_receipt(
        state="SP",
        seller_id=seller.cnpj,
        date=datetime.now()
        - timedelta(
            days=30,
        ),
    )
    new_receipt = random_receipt(
        state="MG",
        seller_id=seller.cnpj,
        date=datetime.now(),
    )
    await repo.add(old_receipt)
    await repo.add(new_receipt)
    result = await repo.query(filter={"sort": "-date"})
    ranking = sorted(
        [i for i in result if i.date is not None],
        key=operator.attrgetter(
            "date",
        ),
        reverse=True,
    )
    assert result[: len(ranking)] == ranking
    result = await repo.query(filter={"sort": "date"})
    ranking = sorted(
        [i for i in result if i.date is not None],
        key=operator.attrgetter(
            "date",
        ),
    )
    assert result[: len(ranking)] == ranking
    result = await repo.query(filter={"sort": "state"})
    ranking = sorted(
        [i for i in result if i.state is not None],
        key=operator.attrgetter(
            "state",
        ),
    )
    assert result[: len(ranking)] == ranking


async def test_can_skip(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await seller_repo.add(seller_1)
    await seller_repo.add(seller_2)
    receipt_repo = ReceiptRepo(async_pg_session)
    receipt_1 = random_receipt(seller_id=seller_1.cnpj)
    receipt_2 = random_receipt(seller_id=seller_2.cnpj)
    await receipt_repo.add(receipt_1)
    await receipt_repo.add(receipt_2)
    all = await receipt_repo.query()
    skipped = await receipt_repo.query(filter={"skip": 1})
    assert len(list(all)) - len(list(skipped)) == 1


async def test_can_limit(async_pg_session: AsyncSession):
    seller_repo = SellerRepo(async_pg_session)
    seller_1 = random_seller()
    seller_2 = random_seller()
    await seller_repo.add(seller_1)
    await seller_repo.add(seller_2)
    receipt_repo = ReceiptRepo(async_pg_session)
    receipt_1 = random_receipt(seller_id=seller_1.cnpj)
    receipt_2 = random_receipt(seller_id=seller_2.cnpj)
    await receipt_repo.add(receipt_1)
    await receipt_repo.add(receipt_2)
    result = await receipt_repo.query(filter={"limit": 1})
    assert len(list(result)) == 1
