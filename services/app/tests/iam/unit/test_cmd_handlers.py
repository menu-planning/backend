import pytest
from src.contexts.iam.core.domain import commands
from src.contexts.iam.core.domain.enums import Role as EnumRoles
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.iam.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.iam.core.bootstrap.bootstrap import bootstrap
from tests.iam.random_refs import random_create_user_classmethod_kwargs
from tests.iam.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus() -> MessageBus:
    uow = FakeUnitOfWork()
    return bootstrap(uow)


class TestCreateUser:
    async def test_for_new_user(self):
        bus_test = bus()
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None


class TestAssignRole:
    async def test_new_role(self):
        bus_test = bus()
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        
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
        
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert user.has_role("IAM", EnumRoles.ADMINISTRATOR)


class TestRemoveRole:
    async def test_remove_role(self):
        bus_test = bus()
        kwargs = random_create_user_classmethod_kwargs(prefix="test_cmd_handlers")
        cmd = commands.CreateUser(
            user_id=kwargs["id"],
        )
        await bus_test.handle(cmd)
        
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
        
        async with bus_test.uow as uow:
            user = await uow.users.get(cmd.user_id)
            assert user is not None
            assert not user.has_role("IAM", EnumRoles.USER)
