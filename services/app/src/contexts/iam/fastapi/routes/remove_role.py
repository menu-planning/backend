from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.iam.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.iam.fastapi.deps import current_active_user
from src.contexts.iam.shared.adapters.api_schemas.commands.remove_role_from_user import (
    ApiRemoveRoleFromUser,
)
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.domain.enums import Permission as EnumPermissions
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory

router = APIRouter()


@router.post(
    "/users/remove-role",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def remove_role(
    cmd_data: ApiRemoveRoleFromUser,
    current_user: Annotated[User, Depends(current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Remove a role from a user.
    """
    if not current_user.has_permission("IAM", EnumPermissions.MANAGE_USERS.value):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    cmd = cmd_data.to_domain()
    await bus.handle(cmd)
