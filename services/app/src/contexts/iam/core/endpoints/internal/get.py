import json
from typing import Any

from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiUser
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

container = Container()


async def get(id: str, caller_context: str) -> dict[str, int | str]:
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            user = await uow.users.get(id)
        except EntityNotFoundException:
            logger.error(f"User not found in database: {id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "User not in database."}),
            }
        except MultipleEntitiesFoundException:
            logger.error(f"Multiple users found in database: {id}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Multiple users found in database."}),
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error."}),
            }
        return _get_user_data_with_right_context_roles(user, caller_context)


def _get_user_data_with_right_context_roles(user: User, caller_context: str) -> dict[str, int | str]:
    api_user = ApiUser.from_domain(user)
    all_roles = [i for i in api_user.roles]
    caller_context_roles = []
    if all_roles:
        for role in all_roles:
            if role.context == caller_context:
                caller_context_roles.append(role)
    new_api_user = api_user.model_copy(update={"roles": frozenset(caller_context_roles)})
    return {"statusCode": 200} | {"body": new_api_user.model_dump_json(include={'id', 'roles'}, exclude={"roles":{"context"}})}
