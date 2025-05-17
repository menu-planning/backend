import traceback
from datetime import UTC, datetime

import anyio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.iam.core.services.uow import UnitOfWork
from tests.iam.random_refs import random_user

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def insert_user(session: AsyncSession, id, version=1):
    role_stmt = """INSERT INTO iam.roles (name, context, permissions) 
    VALUES (:name, :context, :permissions) 
    ON CONFLICT (name, context) DO NOTHING"""
    role_dict = {
        "name": "User",
        "context": "IAM",
        "permissions": "access_basic_features",
    }
    user_stmt = """INSERT INTO iam.users (id, version, discarded, 
      created_at, updated_at) VALUES (:id, :version, :discarded, 
      :created_at, :updated_at) ON CONFLICT (id) DO NOTHING"""
    user_dict = {
        "id": id,
        "version": version,
        "discarded": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    association_stmt = """INSERT INTO iam.user_role_association (user_id, role_name, role_context)
    VALUES (:user_id, :role_name, :role_context) ON CONFLICT (user_id, role_name, role_context) DO NOTHING"""
    association_dict = {"user_id": id, "role_name": "User", "role_context": "IAM"}

    await session.execute(text(role_stmt), role_dict)
    await session.execute(text(user_stmt), user_dict)
    await session.execute(text(association_stmt), association_dict)


async def test_uow_can_retrieve_a_user_and_asign_role(async_pg_session_factory):
    user = random_user(prefix="test_uow")
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await insert_user(
            session,
            user.id,
            user.version,
        )
        await session.commit()
    async with UnitOfWork(async_pg_session_factory) as uow:
        user = await uow.users.get(user.id)
        assert not user.has_role("IAM", Role.role_manager())
        user.assign_role(Role.role_manager())
        await uow.users.persist(user)
        await uow.commit()
    async with async_pg_session_factory() as session:
        assert user.has_role("IAM", Role.role_manager())


async def test_rolls_back_uncommitted_work_by_default(async_pg_session_factory):
    user = random_user(prefix="test_uow")
    async with UnitOfWork(async_pg_session_factory) as uow:
        await insert_user(
            uow.session,
            user.id,
            user.version,
        )
    new_session: AsyncSession
    async with async_pg_session_factory() as new_session:
        result = await new_session.execute(
            text(f"SELECT * FROM iam.users WHERE id=:id"), {"id": user.id}
        )
        assert list(result) == []


async def test_rolls_back_on_error(async_pg_session_factory):
    class MyException(Exception):
        pass

    user = random_user(prefix="test_uow")
    with pytest.raises(MyException):
        async with UnitOfWork(async_pg_session_factory) as uow:
            await insert_user(
                uow.session,
                user.id,
                user.version,
            )
            raise MyException()
    new_session: AsyncSession
    async with async_pg_session_factory() as new_session:
        result = await new_session.execute(
            text(f"SELECT * FROM iam.users WHERE id=:id"), {"id": user.id}
        )
        assert list(result) == []


async def try_to_assign_role(id, exceptions, session_factory, hash, idle_time=0):
    try:
        async with UnitOfWork(session_factory) as uow:
            user = await uow.users.get(id)
            print(f"start -> {user.version} / {hash}")
            user.assign_role(Role.role_manager())
            await uow.users.persist(user)
            await anyio.sleep(idle_time)
            user = await uow.users.get(id)
            print(f"end -> {user.version} / {hash}")
            await uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


async def test_concurrent_updates_to_version_are_not_allowed(
    async_pg_session_factory,
):
    user = random_user(prefix="test_uow")
    old_version = user.version
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await insert_user(
            session,
            user.id,
            user.version,
        )
        await session.commit()
    exceptions: list[Exception] = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            try_to_assign_role, user.id, exceptions, async_pg_session_factory, "1", 1
        )
        tg.start_soon(
            try_to_assign_role,
            user.id,
            exceptions,
            async_pg_session_factory,
            "2",
        )

    [[version]] = await session.execute(
        text("SELECT version FROM iam.users WHERE id=:id"),
        {"id": user.id},
    )
    await session.close()
    assert version == old_version + 1
    [exception] = exceptions
    assert "could not serialize access due to concurrent update" in str(exception)
