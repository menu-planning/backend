import threading

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts._receipt_tracker.shared.adapters.api_schemas.entities.receipt import (
    ApiReceipt,
)
from src.contexts._receipt_tracker.shared.adapters.repositories.receipt import (
    ReceiptRepo,
)
from src.contexts._receipt_tracker.shared.endpoints.internal.internal import get
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.endpoints.exceptions import InvalidApiSchemaException
from src.db.database import async_db
from tests.receipt_tracker.random_refs import random_cfe_key, random_receipt

pytestmark = [pytest.mark.anyio, pytest.mark.e2e]


async def test_existing_cfe_key(async_pg_session: AsyncSession):
    repo = ReceiptRepo(async_pg_session)
    receipt = random_receipt()
    await repo.add(receipt)
    print(threading.active_count())
    print(async_db._engine.pool.status())
    await repo._session.commit()
    assert await get(receipt.id) == ApiReceipt.from_domain(receipt).model_dump_json()


async def test_can_list_receipt_by_house_id(async_pg_session: AsyncSession):
    repo = ReceiptRepo(async_pg_session)
    receipt = random_receipt()
    print(threading.active_count())
    print(async_db._engine.pool.status())
    await repo.add(receipt)
    receipt_2 = random_receipt()
    await repo.add(receipt_2)
    await repo._session.commit()
    assert await repo.list_by_house_id(receipt.house_ids[0]) == [receipt]


async def test_nonexistent_cfe_key():
    with pytest.raises(EntityNotFoundException):
        await get(random_cfe_key(35))


async def test_not_44_cfe_key():
    with pytest.raises(InvalidApiSchemaException):
        await get("invalid")


async def test_unknown_state_cfe_key():
    with pytest.raises(InvalidApiSchemaException):
        await get(f"99{'0'*42}")
