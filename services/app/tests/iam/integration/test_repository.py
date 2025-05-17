import pytest
from sqlalchemy.exc import IntegrityError
from src.contexts.iam.core.adapters.repositories.user import UserRepo
from src.contexts.iam.core.domain.entities.user import User
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from tests.iam.random_refs import random_user

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_unique_column_works(async_pg_session):
    repo = UserRepo(async_pg_session)
    user_1 = random_user(prefix="test_repo-")
    same_name = User(
        id=user_1.id,
    )
    await repo.add(user_1)
    with pytest.raises(IntegrityError):
        await repo.add(same_name)


async def test_cannot_persist_user_not_added(async_pg_session):
    repo = UserRepo(async_pg_session)
    user = random_user(prefix="test_repo-")
    with pytest.raises(AssertionError):
        await repo.persist(user)


async def test_can_list_with_empty_filter(async_pg_session):
    repo = UserRepo(async_pg_session)
    user_1 = random_user(prefix="test_repo_list_empty_1")
    user_2 = random_user(prefix="test_repo_list_empty_2")
    await repo.add(user_1)
    await repo.add(user_2)
    await repo._session.commit()
    result = await repo.query()
    assert user_1 in result
    assert user_2 in result


async def test_can_list_with_allowed_filter(async_pg_session):
    repo = UserRepo(async_pg_session)
    user = random_user(prefix="test_repo_list_allowed")
    await repo.add(user)
    exist = await repo.query(filter={"context": "IAM"})
    do_not_exist = await repo.query(filter={"context": "INVALID"})
    assert user in exist
    assert len(list(do_not_exist)) == 0


async def test_cannot_use_not_allowed_filter(async_pg_session):
    repo = UserRepo(async_pg_session)
    with pytest.raises(BadRequestException):
        await repo.query(filter={"not_allowed": "not_allowed"})


async def test_can_skip(async_pg_session):
    repo = UserRepo(async_pg_session)
    user_1 = random_user(prefix="test_repo-")
    user_2 = random_user(prefix="test_repo-")
    await repo.add(user_1)
    await repo.add(user_2)
    all = await repo.query()
    skipped = await repo.query(filter={"skip": 1})
    assert len(list(all)) - len(list(skipped)) == 1


async def test_can_limit(async_pg_session):
    repo = UserRepo(async_pg_session)
    user_1 = random_user(prefix="test_repo-")
    user_2 = random_user(prefix="test_repo-")
    await repo.add(user_1)
    await repo.add(user_2)
    result = await repo.query(filter={"limit": 1})
    assert len(list(result)) == 1
