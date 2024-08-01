from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.commands.items.commands_api_schema import (
    ApiDiscardItems,
)
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.item import ApiItem
from src.contexts.food_tracker.shared.domain.enums import Permission
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.exceptions import ForbiddenException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.post(
    "/food-items/houses/{house_id}/discard", status_code=status.HTTP_201_CREATED
)
async def discard_from_house(
    house_id: Annotated[int, Path(title="The ID of the house to update")],
    api: ApiDiscardItems,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Discard items.
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
        for item_id in api.item_ids:
            item = await uow.items.get(item_id)
            if house_id != item.house_id:
                raise HTTPException(status_code=404, detail="Item not found in house.")
    cmd = api.to_domain()
    await bus.handle(cmd)
