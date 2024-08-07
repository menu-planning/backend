from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.house import (
    ApiHouse,
)
from src.contexts.food_tracker.shared.domain.enums import Permission
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.seedwork.shared.endpoints.exceptions import ForbiddenException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.get(
    "/houses/{house_id}",
    # response_model=ApiHouse,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def read_specific_house(
    house_id: Annotated[int, Path(title="The ID of the house to update")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiHouse:
    """
    Retrieve specific house.
    """
    uow: UnitOfWork
    with bus.uow as uow:
        house = await uow.houses.get(house_id)
    if not (
        current_user.has_permission(Permission.MANAGE_HOUSES)
        or current_user.id == house.owner_id
        or current_user.id in house.members_ids
        or current_user.id in house.nutritionists_ids
    ):
        raise ForbiddenException()
    return ApiHouse.from_domain(house)
