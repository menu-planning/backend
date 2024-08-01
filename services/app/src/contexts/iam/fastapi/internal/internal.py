import json
from typing import Annotated, Any

from fastapi import Depends
from src.contexts.iam.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.iam.fastapi.deps import (
    current_active_user as deps_current_active_user,
)
from src.contexts.iam.shared.adapters.api_schemas.entities.user import ApiUser
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


class CurrentActiveUserWithContext:
    def __init__(self, caller_context: str):
        self.caller_context = caller_context

    def __call__(
        self, current_active_user: Annotated[User, Depends(deps_current_active_user)]
    ) -> str:
        user_json = _get_user_data_with_right_context_roles(
            current_active_user, self.caller_context
        )
        return user_json


async def get(id: str, caller_context: str) -> str:
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    uow: UnitOfWork
    async with bus.uow as uow:
        user = await uow.users.get(id)
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
    return json.dumps(user_data)
