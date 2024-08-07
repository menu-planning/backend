from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.iam.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.iam.fastapi.deps import current_active_user
from src.contexts.iam.shared.adapters.api_schemas.commands.assign_role_to_user import (
    ApiAssignRoleToUser,
)
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.domain.enums import Permission as EnumPermissions
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.post(
    "/users/assign-role",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def assign_role(
    cmd_data: ApiAssignRoleToUser,
    current_user: Annotated[User, Depends(current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Assign a role to a user.
    """
    if not current_user.has_permission("IAM", EnumPermissions.MANAGE_USERS.value):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = cmd_data.to_domain()
    await bus.handle(cmd)
