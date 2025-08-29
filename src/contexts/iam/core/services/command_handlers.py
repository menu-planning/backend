from src.contexts.iam.core.domain.commands import (
    AssignRoleToUser,
    CreateUser,
    RemoveRoleFromUser,
)
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from src.logging.logger import logger


async def create_user(cmd: CreateUser, uow: UnitOfWork) -> None:
    async with uow:
        try:
            await uow.users.get(entity_id=cmd.user_id)
        except EntityNotFoundError:
            user = User.create_user(
                entity_id=cmd.user_id,
            )
            await uow.users.add(user)
            await uow.commit()
        else:
            logger.info(f"User with id {cmd.user_id} already exists.")
            raise MultipleEntitiesFoundError(
                entity_id=cmd.user_id, repository=uow.users._generic_repo
            )


async def assign_role_to_user(cmd: AssignRoleToUser, uow: UnitOfWork) -> None:
    async with uow:
        user = await uow.users.get(cmd.user_id)
        user.assign_role(cmd.role)
        await uow.users.persist(user)
        await uow.commit()


async def remove_role_from_user(cmd: RemoveRoleFromUser, uow: UnitOfWork) -> None:
    async with uow:
        user = await uow.users.get(cmd.user_id)
        user.remove_role(cmd.role)
        await uow.users.persist(user)
        await uow.commit()
