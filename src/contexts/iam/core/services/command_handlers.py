"""Command handlers for IAM domain actions.

Application services that execute IAM use cases by coordinating domain operations
with persistence through the UnitOfWork pattern.
"""

from src.contexts.iam.core.domain.commands import (
    AssignRoleToUser,
    CreateUser,
    RemoveRoleFromUser,
)
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.services.uow import UnitOfWork
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


async def create_user(cmd: CreateUser, uow: UnitOfWork) -> None:
    """Execute the create user use case.

    Args:
        cmd: Command containing user_id (UUID v4) for the new user.
        uow: UnitOfWork instance for transaction management.

    Returns:
        None: User creation is a side-effect operation.

    Raises:
        MultipleEntitiesFoundError: If user with given ID already exists.
        EntityNotFoundError: Propagated from repository if user lookup fails.

    Events:
        UserCreated: Emitted when user is successfully created.

    Idempotency:
        No. Duplicate calls with same user_id will raise MultipleEntitiesFoundError.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Creates new User aggregate, persists to database.
    """
    async with uow:
        try:
            await uow.users.get(id=cmd.user_id)
        except EntityNotFoundError:
            user = User.create_user(
                id=cmd.user_id,
            )
            await uow.users.add(user)
            await uow.commit()
        else:
            logger.info(
                "User already exists",
                action="create_user_duplicate",
                business_context="user_management",
            )
            raise MultipleEntitiesFoundError(
                id=cmd.user_id, repository=uow.users._generic_repo
            )


async def assign_role_to_user(cmd: AssignRoleToUser, uow: UnitOfWork) -> None:
    """Execute the assign role to user use case.

    Args:
        cmd: Command containing user_id and role to assign.
        uow: UnitOfWork instance for transaction management.

    Returns:
        None: Role assignment is a side-effect operation.

    Raises:
        EntityNotFoundError: If user with given ID does not exist.

    Idempotency:
        Yes. Key: user_id + role. Duplicate calls have no additional effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Updates User aggregate with new role, persists to database.
    """
    async with uow:
        user = await uow.users.get(cmd.user_id)
        user.assign_role(cmd.role)
        await uow.users.persist(user)
        await uow.commit()


async def remove_role_from_user(cmd: RemoveRoleFromUser, uow: UnitOfWork) -> None:
    """Execute the remove role from user use case.

    Args:
        cmd: Command containing user_id and role to remove.
        uow: UnitOfWork instance for transaction management.

    Returns:
        None: Role removal is a side-effect operation.

    Raises:
        EntityNotFoundError: If user with given ID does not exist.

    Idempotency:
        Yes. Key: user_id + role. Duplicate calls have no additional effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Updates User aggregate by removing role, persists to database.
    """
    async with uow:
        user = await uow.users.get(cmd.user_id)
        user.remove_role(cmd.role)
        await uow.users.persist(user)
        await uow.commit()
