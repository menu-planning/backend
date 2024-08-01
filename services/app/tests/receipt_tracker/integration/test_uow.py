import traceback

import anyio
import pytest
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork
from tests.receipt_tracker.random_refs import (
    random_attr,
    random_cfe_key,
    random_cnpj,
    random_item,
    random_receipt,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def insert_seller(session: AsyncSession, id: str):
    seller_stmt = """INSERT INTO receipt_tracker.sellers (id, name, state_registration,
        street, number, zip_code, district, city, state, complement, note)
        VALUES (:id, :name, :state_registration, :street, :number, :zip_code,
        :district, :city, :state, :complement, :note)"""
    seller_dict = {
        "id": id,
        "name": random_attr("seller"),
        "state_registration": random_attr("state_registration"),
        "street": random_attr("street"),
        "number": random_attr("number"),
        "zip_code": random_attr("zip_code"),
        "district": random_attr("district"),
        "city": random_attr("city"),
        "state": "SP",
        "complement": random_attr("complement"),
        "note": random_attr("note"),
    }
    await session.execute(text(seller_stmt), seller_dict)


async def insert_receipt(
    session: AsyncSession,
    cfe_key: str,
    houses: list[str],
    seller_id: str | None = None,
    version=1,
):
    receipt_stmt = """INSERT INTO receipt_tracker.receipts (id, qrcode, date,
        state, seller_id, scraped, products_added, discarded, version)
        VALUES (:id, :qrcode, :date, :state, :seller_id, :scraped, :products_added,
        :discarded, :version)"""
    receipt_dict = {
        "id": cfe_key,
        "qrcode": None,
        "date": None,
        "state": "SP",
        "seller_id": seller_id or None,
        "scraped": True,
        "products_added": False,
        "discarded": False,
        "version": version,
    }
    house_stmt = """INSERT INTO receipt_tracker.houses (id) VALUES (:id)"""
    association_stmt = """INSERT INTO receipt_tracker.receipts_houses_association
        (house_id, receipt_id) VALUES (:house_id, :receipt_id)"""

    await session.execute(text(receipt_stmt), receipt_dict)
    for house_id in houses:
        await session.execute(text(house_stmt), {"id": house_id})
        await session.execute(
            text(association_stmt), {"house_id": house_id, "receipt_id": cfe_key}
        )


async def clean_db(session: AsyncSession):
    await session.execute(
        text("DELETE FROM receipt_tracker.receipts_houses_association")
    )
    await session.execute(text("DELETE FROM receipt_tracker.items"))
    await session.execute(text("DELETE FROM receipt_tracker.receipts"))
    await session.execute(text("DELETE FROM receipt_tracker.sellers"))
    await session.execute(text("DELETE FROM receipt_tracker.houses"))
    await session.commit()


# async def get_user_confirmed_attribute(session, id):
#     stmt = "SELECT confirmed FROM iam.users WHERE id=:id"
#     result = await session.execute(text(stmt), {"id": id})
#     return result.scalar_one()


async def test_uow_can_retrieve_a_receipt_and_update_it(async_pg_session_factory):
    cfe_key = random_cfe_key(35)
    house_id = random_attr("id")
    seller_id = str(random_cnpj())
    async with UnitOfWork(async_pg_session_factory) as uow:
        await insert_seller(
            uow.session,
            seller_id,
        )
        await insert_receipt(
            uow.session,
            cfe_key=cfe_key,
            houses=[house_id],
            seller_id=seller_id,
        )
        receipt = await uow.receipts.get(cfe_key)
        item = random_item()
        seller = await uow.sellers.get(seller_id)
        receipt.add_items([item])
        receipt.seller_id = seller.cnpj
        await uow.receipts.persist(receipt)
        receipt = await uow.receipts.get(cfe_key)
        assert receipt.seller_id == seller.cnpj
        assert len(receipt.items) == 1


async def test_uow_can_retrieve_a_seller(async_pg_session_factory):
    seller_id = str(random_cnpj())
    async with UnitOfWork(async_pg_session_factory) as uow:
        await insert_seller(
            uow.session,
            seller_id,
        )
        seller = await uow.sellers.get(seller_id)
        assert str(seller.cnpj) == seller_id


async def test_rolls_back_uncommitted_work_by_default(async_pg_session_factory):
    cfe_key = random_cfe_key(35)
    house_id = random_attr("id")
    seller_id = str(random_cnpj())
    async with UnitOfWork(async_pg_session_factory) as uow:
        await insert_seller(
            uow.session,
            seller_id,
        )
        await insert_receipt(
            uow.session,
            cfe_key=cfe_key,
            houses=[house_id],
            seller_id=seller_id,
        )
    new_session: AsyncSession
    async with async_pg_session_factory() as new_session:
        with pytest.raises(NoResultFound):
            receipt = await new_session.execute(
                text(f"SELECT * FROM receipt_tracker.receipts WHERE id=:id"),
                {"id": cfe_key},
            )
            receipt.scalar_one()
        with pytest.raises(NoResultFound):
            seller = await new_session.execute(
                text(f"SELECT * FROM receipt_tracker.sellers WHERE id=:id"),
                {"id": seller_id},
            )
            seller.scalar_one()


async def test_rolls_back_on_error(async_pg_session_factory):
    class MyException(Exception):
        pass

    cfe_key = random_cfe_key(35)
    house_id = random_attr("id")
    seller_id = str(random_cnpj())
    with pytest.raises(MyException):
        async with UnitOfWork(async_pg_session_factory) as uow:
            await insert_seller(
                uow.session,
                seller_id,
            )
            await insert_receipt(
                uow.session,
                cfe_key=cfe_key,
                houses=[house_id],
                seller_id=seller_id,
            )
            raise MyException()
    new_session: AsyncSession
    async with async_pg_session_factory() as new_session:
        receipt = await new_session.execute(
            text(f"SELECT * FROM receipt_tracker.receipts WHERE id=:id"),
            {"id": cfe_key},
        )
        assert list(receipt) == []
        seller = await new_session.execute(
            text(f"SELECT * FROM receipt_tracker.sellers WHERE id=:id"),
            {"id": seller_id},
        )
        assert list(seller) == []


async def try_to_add_qrcode(id, exceptions, session_factory, idle_time=0):
    try:
        async with UnitOfWork(session_factory) as uow:
            receipt = await uow.receipts.get(id)
            receipt.qrcode = random_attr("qrcode")
            await uow.receipts.persist(receipt)
            await anyio.sleep(idle_time)
            await uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


async def test_concurrent_updates_to_version_are_not_allowed(
    async_pg_session_factory,
):
    receipt = random_receipt()
    old_version = receipt.version
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await insert_receipt(
            session,
            cfe_key=receipt.id,
            houses=[random_attr("house_id")],
            version=receipt.version,
        )
        await session.commit()
    exceptions: list[Exception] = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            try_to_add_qrcode, receipt.id, exceptions, async_pg_session_factory, 1
        )
        tg.start_soon(
            try_to_add_qrcode, receipt.id, exceptions, async_pg_session_factory
        )

    [[version]] = await session.execute(
        text("SELECT version FROM receipt_tracker.receipts WHERE id=:id"),
        {"id": receipt.id},
    )
    await session.close()
    assert version == old_version + 1
    [exception] = exceptions
    assert "could not serialize access due to concurrent update" in str(exception)
    async with async_pg_session_factory() as session:
        await clean_db(session)
