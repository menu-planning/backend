import time
from datetime import datetime

import pytest
from anyio import create_task_group
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.api_config import api_settings
from src.config.app_config import app_settings
from src.contexts.iam.core.domain.entities.user import User
from src.contexts.iam.core.domain.value_objects.role import Role
from src.db.database import async_db
from tests.iam.e2e.result_gathering import ResultGatheringTaskgroup
from tests.iam.random_refs import random_attr, random_user

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.e2e,
    # pytest.mark.usefixtures("async_pg_db"),
]

URL_PREFIX = api_settings.api_v1_str


async def _insert_user(
    session: AsyncSession,
    id,
    role_name: str = "user",
    permissions: str = "access_basic_features",
    version=1,
):
    role_stmt = """INSERT INTO iam.roles (name, context, permissions) 
    VALUES (:name, :context, :permissions) 
    ON CONFLICT (name, context) DO NOTHING"""
    role_dict = {
        "name": role_name,
        "context": "IAM",
        "permissions": permissions,
    }
    user_stmt = """INSERT INTO iam.users (id, version, discarded, created_at, 
      updated_at) VALUES (:id, :version, :discarded, :created_at, :updated_at)
      ON CONFLICT (id) DO NOTHING"""
    user_dict = {
        "id": id,
        "version": version,
        "discarded": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    association_stmt = """INSERT INTO iam.user_role_association (user_id, role_name, role_context)
    VALUES (:user_id, :role_name, :role_context) ON CONFLICT DO NOTHING"""
    association_dict = {"user_id": id, "role_name": role_name, "role_context": "IAM"}

    await session.execute(text(role_stmt), role_dict)
    await session.execute(text(user_stmt), user_dict)
    await session.execute(text(association_stmt), association_dict)


async def test_happy_path_returns_201_and_create_user(
    make_client_with_user_id,
):
    user_id = random_attr("id")
    async with make_client_with_user_id(user_id) as client:
        response = await client.post(
            f"{URL_PREFIX}/users",
            json={
                "user_id": user_id,
            },
        )
    assert response.status_code == 201


async def test_existing_user_id_return_error(
    make_client_with_user_id,
    async_pg_session_factory,
):
    user_id = random_attr("id")
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await _insert_user(
            session,
            user_id,
        )
        await session.commit()
    async with make_client_with_user_id(user_id) as client:
        response_error = await client.post(
            f"{URL_PREFIX}/users",
            json={
                "user_id": user_id,
            },
        )
        assert response_error.status_code == 409


def _deep_dict_equal(dict1, dict2):
    """
    Recursively checks if two dictionaries are equal, accounting for nested dictionaries
    and lists containing dictionaries as their items.
    """
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        if dict1.keys() != dict2.keys():
            return False
        for key in dict1:
            if not _deep_dict_equal(dict1[key], dict2[key]):
                return False
        return True
    elif isinstance(dict1, list) and isinstance(dict2, list):
        # Ensure both lists contain the same dictionaries, regardless of order
        if len(dict1) != len(dict2):
            return False
        for item in dict1:
            # Check each item in dict1 to see if there is an equivalent in dict2
            if isinstance(item, dict):
                if not any(_deep_dict_equal(item, d2_item) for d2_item in dict2):
                    return False
            else:
                # For non-dict items, just ensure the item is present in dict2
                if item not in dict2:
                    return False
        return True
    else:
        return dict1 == dict2


class TestAssignRole:
    async def test_regular_user_cannot_assign_role(
        self,
        make_client_with_active_user,
        async_pg_session_factory,
    ):
        user: User = random_user(id="test_user")
        session: AsyncSession
        async with async_pg_session_factory() as session:
            await _insert_user(
                session=session,
                id=user.id,
            )
            await session.commit()

        async with make_client_with_active_user(user) as client:
            response = await client.post(
                f"{URL_PREFIX}/users/assign-role",
                json={
                    "user_id": user.id,
                    "role": {
                        "name": "test-user",
                        "context": "test-context",
                        "permissions": ["test-permissions"],
                    },
                },
            )
            assert response.status_code == 403

    async def test_admin_can_assign_role(
        self,
        make_client_with_active_user,
        async_pg_session_factory,
    ):
        user: User = random_user(id="user_id")
        session: AsyncSession
        async with async_pg_session_factory() as session:
            await _insert_user(
                session=session,
                id=user.id,
            )
            await session.commit()

        manager: User = random_user(id="manager_id")
        manager.assign_role(role=Role.user_manager())
        role_to_assign = {
            "name": "test-user",
            "context": "test-context",
            "permissions": ["test-permissions"],
        }
        async with make_client_with_active_user(manager) as client:
            response = await client.post(
                f"{URL_PREFIX}/users/assign-role",
                json={
                    "user_id": user.id,
                    "role": role_to_assign,
                },
            )
            assert response.status_code == 200

            response = await client.get(
                f"{URL_PREFIX}/users/{user.id}",
            )
            assert response.status_code == 200
            role_assigned = False
            for role in response.json()["roles"]:
                if _deep_dict_equal(role, role_to_assign):
                    role_assigned = True
            assert role_assigned


async def test_connection_pool_size(
    make_client_with_user_id: AsyncClient,
    async_pg_session_factory,
):
    user_id = random_attr("test_pool_size")
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await _insert_user(
            session,
            user_id,
        )
        await session.commit()

    times = 10
    url = f"{URL_PREFIX}/users/{user_id}"
    async with make_client_with_user_id(user_id) as client:
        async with create_task_group() as g:
            for _ in range(times):
                g.start_soon(client.get, url)
    assert (
        f"Connections in pool: {app_settings.sa_pool_size}"
        in async_db._engine.pool.status()
    )


async def test_multiple_requests(
    make_client_with_user_id: AsyncClient,
    async_pg_session_factory,
):
    user_id = random_attr("test_pool_size")
    session: AsyncSession
    async with async_pg_session_factory() as session:
        await _insert_user(
            session,
            user_id,
        )
        await session.commit()

    times = 100
    url = f"{URL_PREFIX}/users/{user_id}"
    t0 = time.perf_counter()

    async with make_client_with_user_id(user_id) as client:
        async with ResultGatheringTaskgroup() as tg:
            for _ in range(times):
                await tg.start(client.get, url)
    elapsed = time.perf_counter() - t0
    assert len(tg.result) == times
    ids = set([u["id"] for u in [r.json() for r in tg.result]])
    assert len(ids) == 1
    assert user_id in ids
    assert elapsed < times * 0.05
