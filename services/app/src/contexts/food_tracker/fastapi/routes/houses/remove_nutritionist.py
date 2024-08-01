from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.commands.houses.commands_api_schema import (
    ApiRemoveNutritionist,
)
from src.contexts.food_tracker.shared.domain.enums import Permission
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.exceptions import ForbiddenException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.post(
    "/houses/{house_id}/remove-nutritionist", status_code=status.HTTP_201_CREATED
)
async def remove_nutritionist(
    house_id: Annotated[int, Path(title="The ID of the house to update")],
    api: ApiRemoveNutritionist,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Remove a nutritionist from a house.
    """
    uow: UnitOfWork
    with bus.uow as uow:
        house = await uow.houses.get(house_id)
    if not (
        current_user.has_permission(Permission.MANAGE_HOUSES)
        or current_user.id == house.owner_id
    ):
        raise ForbiddenException()
    cmd = api.to_domain(house_id=house_id)
    await bus.handle(cmd)
