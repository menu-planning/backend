import json
from unittest import mock

import pytest
from aio_pika import Message, RobustChannel
from src.config.app_config import app_settings
from src.contexts.iam.fastapi.bootstrap import fastapi_bootstrap, get_aio_pika_manager
from src.contexts.iam.core.domain import commands
from src.contexts.iam.core.rabbitmq_data import email_admin_new_user_data
from src.contexts.iam.core.services.uow import UnitOfWork
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


class TestUserCreated:
    async def test_for_unverified_user(
        self,
    ):
        kwargs = random_create_user_classmethod_kwargs(prefix="test_evt_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        await bus.handle(cmd)
        uow: UnitOfWork
        async with bus.uow as uow:
            user = await uow.users.get(kwargs["id"])

        assert user is not None
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
