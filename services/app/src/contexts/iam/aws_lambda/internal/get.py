import json
from typing import Any

from src.contexts.iam.shared.adapters.api_schemas.entities.user import ApiUser
from src.contexts.iam.shared.bootstrap.container import Container
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

container = Container()


async def get(id: str, caller_context: str) -> str:
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            user = await uow.users.get(id)
        except EntityNotFoundException:
            logger.error(f"User not found in database: {id}")
            return json.dumps({"statuCode": 404, "body": "User not in database."})
        except MultipleEntitiesFoundException:
            logger.error(f"Multiple users found in database: {id}")
            return json.dumps(
                {"statuCode": 500, "body": "Multiple users found in database."}
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            return json.dumps({"statuCode": 500, "body": "Internal server error."})
        return _get_user_data_with_right_context_roles(user, caller_context)


def _get_user_data_with_right_context_roles(user: User, caller_context: str) -> str:
    user_data: dict[str, Any] = ApiUser.from_domain(user).model_dump()
    all_roles = user_data.get("roles")
    caller_context_roles = []
    if all_roles:
        for role in all_roles:
            if role.get("context") == caller_context:
                caller_context_roles.append(role)
    user_data["roles"] = caller_context_roles
    return json.dumps({"statusCode": 200} | user_data)
