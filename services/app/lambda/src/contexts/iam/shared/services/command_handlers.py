from src.contexts.iam.shared.domain.commands import AssignRoleToUser, CreateUser
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.logging.logger import logger


async def create_user(cmd: CreateUser, uow: UnitOfWork) -> None:
    async with uow:
        try:
            await uow.users.get(id=cmd.user_id)
        except EntityNotFoundException:
            user = User.create_user(
                id=cmd.user_id,
            )
            await uow.users.add(user)
            await uow.commit()
        else:
            logger.info(f"User with id {cmd.user_id} already exists.")
            raise MultipleEntitiesFoundException(
                entity_id=cmd.user_id, repository=uow.users
            )


async def assign_role_to_user(cmd: AssignRoleToUser, uow: UnitOfWork) -> None:
    async with uow:
        user = await uow.users.get(cmd.user_id)
        user.assign_role(cmd.role)
        await uow.users.persist(user)
        await uow.commit()


async def remove_role_from_user(cmd: AssignRoleToUser, uow: UnitOfWork) -> None:
    async with uow:
        user = await uow.users.get(cmd.user_id)
        user.remove_role(cmd.role)
        await uow.users.persist(user)
        await uow.commit()
