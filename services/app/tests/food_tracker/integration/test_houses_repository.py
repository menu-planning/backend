import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.food_tracker.shared.adapters.repositories.houses import HousesRepo
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from tests.food_tracker.random_refs import random_house, random_receipt

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_unique_column_works(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house = random_house()
    same_id = random_house()
    same_id._id = house.id
    await repo.add(house)
    with pytest.raises(IntegrityError):
        await repo.add(same_id)
        await async_pg_session.commit()


async def test_cannot_persist_house_not_added(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house = random_house()
    with pytest.raises(AssertionError):
        await repo.persist(house)


async def test_members_to_multiple_houses_merges_successfully(
    async_pg_session: AsyncSession,
):
    repo = HousesRepo(async_pg_session)
    house = random_house(prefix="test_merge_members-")
    member_id = uuid.uuid4().hex
    house.invite_member(member_id)
    house_2 = random_house(prefix="test_merge_members-")
    house_2.invite_member(member_id)
    await repo.add(house)
    await repo.add(house_2)
    await repo._session.commit()
    house = await repo.get(house.id)
    house_2 = await repo.get(house_2.id)
    assert house.members_ids == house_2.members_ids


async def test_receipt_to_multiple_houses_merges_successfully(
    async_pg_session: AsyncSession,
):
    repo = HousesRepo(async_pg_session)
    house_1 = random_house()
    receipt_1 = random_receipt(cfe_key="test_can_filter_by_cfe_key")
    house_1.add_receipt(receipt=receipt_1)
    house_2 = random_house()
    receipt_2 = random_receipt(cfe_key="test_can_filter_by_cfe_key")
    house_2.add_receipt(receipt=receipt_2)
    await repo.add(house_1)
    await repo.add(house_2)
    assert [house_1] == await repo.query(filter={"id": house_1.id})
    assert [house_2] == await repo.query(filter={"id": house_2.id})


async def test_can_filter_by_cfe_key(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house = random_house()
    receipt = random_receipt(cfe_key="test_can_filter_by_cfe_key")
    house.add_receipt(receipt=receipt)
    house_2 = random_house()
    await repo.add(house)
    await repo.add(house_2)
    await repo._session.commit()
    house = await repo.get(house.id)
    assert house.pending_receipts == {receipt}
    result = await repo.query(filter={"cfe_key": receipt.cfe_key})
    assert house in result
    assert house_2 not in result
    assert house.pending_receipts == result[0].pending_receipts
    assert house.added_receipts == result[0].added_receipts


async def test_can_filter_by_members(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house = random_house()
    member_id = uuid.uuid4().hex
    house.invite_member(member_id)
    house_2 = random_house()
    await repo.add(house)
    await repo.add(house_2)
    await repo._session.commit()
    house = await repo.get(house.id)
    assert house.members_ids == {member_id}
    result = await repo.query(filter={"members": member_id})
    assert house in result
    assert house_2 not in result
    assert house.members_ids == result[0].members_ids


async def test_can_filter_by_nutritionists(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house = random_house()
    nutritionist_ids = uuid.uuid4().hex
    house.invite_nutritionist(nutritionist_ids)
    house_2 = random_house()
    await repo.add(house)
    await repo.add(house_2)
    await repo._session.commit()
    house = await repo.get(house.id)
    assert house.nutritionists_ids == {nutritionist_ids}
    result = await repo.query(filter={"nutritionists": nutritionist_ids})
    assert house in result
    assert house_2 not in result
    assert house.nutritionists_ids == result[0].nutritionists_ids


async def test_can_list_with_empty_filter(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house_1 = random_house()
    house_2 = random_house()
    await repo.add(house_1)
    await repo.add(house_2)
    result = await repo.query()
    assert house_1 in result
    assert house_2 in result


async def test_cannot_use_not_allowed_filter(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    with pytest.raises(BadRequestException):
        await repo.query(filter={"not_allowed": "not_allowed"})


async def test_can_list_with_str_or_list(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house_1 = random_house()
    receipt_1 = random_receipt(cfe_key="test_can_filter_by_cfe_key")
    house_1.add_receipt(receipt=receipt_1)
    house_2 = random_house()
    receipt_2 = random_receipt(cfe_key="test_can_filter_by_cfe_key")
    house_2.add_receipt(receipt=receipt_2)
    await repo.add(house_1)
    await repo.add(house_2)
    result = await repo.query(
        filter={"cfe_key": [receipt_1.cfe_key, receipt_2.cfe_key]}
    )
    assert house_1 in result
    assert house_2 in result
    house_1 = await repo.query(filter={"id": house_1.id})
    house_2 = await repo.query(filter={"id": house_2.id})
    assert house_1[0].pending_receipts == {receipt_1}
    assert house_2[0].pending_receipts == {receipt_2}


async def test_can_sort_by_cfe_key(async_pg_session: AsyncSession):
    repo = HousesRepo(async_pg_session)
    house_1 = random_house()
    receipt_1 = random_receipt(cfe_key="test_can_filter_by_cfe_key_1")
    house_1.add_receipt(receipt=receipt_1)
    house_2 = random_house()
    receipt_2 = random_receipt(cfe_key="test_can_filter_by_cfe_key_2")
    house_2.add_receipt(receipt=receipt_2)
    await repo.add(house_1)
    await repo.add(house_2)
    result = await repo.query(filter={"sort": "cfe_key"})
    assert result.index(house_1) < result.index(house_2)
    # result = await repo.select(filter={"sort": "-cfe_key"})
    # assert result.index(house_1) > result.index(house_2)
