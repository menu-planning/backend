"""FastAPI router for role assignment endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.iam.core.adapters.api_schemas.commands.api_assign_role_to_user import (
    ApiAssignRoleToUser,
)
from src.contexts.iam.core.domain.commands import AssignRoleToUser
from src.contexts.iam.core.domain.enums import Permission
from src.contexts.iam.core.domain.root_aggregate.user import User as IAMUser
from src.contexts.iam.fastapi.dependencies import get_iam_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_iam_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/users")

@router.post("/{user_id}/roles")
async def assign_role_to_user(
    user_id: str,
    request_body: ApiAssignRoleToUser,
    current_user: Annotated[IAMUser, Depends(get_iam_user)],
    bus: MessageBus = Depends(get_iam_bus),
) -> Any:
    """Assign a role to a user.
    
    Args:
        user_id: User ID to assign role to
        request_body: Role assignment data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success message confirming role assignment
        
    Raises:
        HTTPException: If user lacks permissions or validation fails
    """
    if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
        error_message = "User does not have enough privileges for role assignment"
        raise PermissionError(error_message)
    
    cmd = request_body.to_domain()
    cmd = AssignRoleToUser(user_id=user_id, role=cmd.role)
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Role assigned successfully"},
        status_code=200
    )
