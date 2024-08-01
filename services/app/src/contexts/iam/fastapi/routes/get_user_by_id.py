from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.iam.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.iam.fastapi.deps import current_active_user
from src.contexts.iam.shared.adapters.api_schemas.entities.user import ApiUser
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.domain.enums import Permission as EnumPermissions
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.get("/users/{user_id}", response_model=ApiUser, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: str,
    current_user: Annotated[User, Depends(current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Get a specific user by id.
    """
    uow: UnitOfWork
    async with bus.uow as uow:
        user = await uow.users.get(id=user_id)
    if user.id == current_user.id:
        return user
    if not current_user.has_permission("IAM", EnumPermissions.MANAGE_USERS.value):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    return user
