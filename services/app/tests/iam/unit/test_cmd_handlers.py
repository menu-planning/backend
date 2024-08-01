import json
from unittest import mock

import pytest
from aio_pika import Message, RobustChannel
from src.config.app_config import app_settings
from src.contexts.iam.fastapi.bootstrap import fastapi_bootstrap, get_aio_pika_manager
from src.contexts.iam.shared.domain import commands
from src.contexts.iam.shared.domain.enums import Role as EnumRoles
from src.contexts.iam.shared.domain.value_objects.role import Role
from src.contexts.iam.shared.rabbitmq_data import email_admin_new_user_data
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_classes import AIOPikaData
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.iam.random_refs import random_create_user_classmethod_kwargs
from tests.iam.unit.fakes import FakeUnitOfWork
from tests.iam.unit.utils import EmailValidator

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


class TestCreateUser:
    async def test_for_new_user(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert uow.committed
        assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 1

        emails = []
        for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
            for arg in list(call.kwargs.values()):
                if isinstance(arg, Message) and hasattr(arg, "body"):
                    msg = json.loads(arg.body.decode())
                    if isinstance(msg, dict):
                        for v in msg.values():
                            try:
                                EmailValidator(email=v)
                                emails.append(v)
                            except Exception:
                                pass

        assert len(emails) == 1
        assert app_settings.first_admin_email in emails

        queue_names = []
        for (
            call
        ) in aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_args_list:
            for arg in list(call.args):
                if isinstance(arg, AIOPikaData):
                    queue_names.append(arg.queue.name)
        assert aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_count == 1
        assert len(queue_names) == 1
        assert email_admin_new_user_data.queue.name in queue_names

    async def test_for_existing_user(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        assert bus_test.uow.committed
        count = aio_pika_manager_mock.publish_from_AIOPikaData.await_count
        assert count == 1


class AssignRole:
    async def test_new_role(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        assert bus_test.uow.committed
        uow: UnitOfWork
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert not user.has_role("IAM", EnumRoles.ADMINISTRATOR)
        role = Role.administrator()
        cmd = commands.AssignRoleToUser(
            user_id=kwargs["id"],
            role=role,
        )
        await bus_test.handle(cmd)
        assert bus_test.uow.committed
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert user.has_role("IAM", EnumRoles.ADMINISTRATOR)


class TestRemoveRole:
    async def test_remove_role(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        assert bus_test.uow.committed
        uow: UnitOfWork
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert user.has_role("IAM", EnumRoles.USER)
        cmd = commands.RemoveRoleFromUser(
            user_id=kwargs["id"],
            role=Role.user(),
        )
        await bus_test.handle(cmd)
        assert bus_test.uow.committed
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert not user.has_role("IAM", EnumRoles.USER)
