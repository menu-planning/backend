from typing import Annotated

from fastapi import APIRouter, Depends, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.commands.items.commands_api_schema import (
    ApiAddItem,
)
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.item import ApiItem
from src.contexts.food_tracker.shared.domain.enums import Permission
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.exceptions import ForbiddenException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.post("/food-items/add", status_code=status.HTTP_201_CREATED)
async def add(
    item_data: ApiAddItem,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    uow: UnitOfWork
    with bus.uow as uow:
        for _ in range(len(item_data.house_ids)):
            house_id = item_data.house_ids.pop()
            house = await uow.houses.get(house_id)
            if not (
                current_user.has_permission(Permission.MANAGE_HOUSES)
                or current_user.id == house.owner_id
                or current_user.id in house.members_ids
                or current_user.id in house.nutritionists_ids
            ):
                raise ForbiddenException()
    cmd = item_data.to_domain()
    await bus.handle(cmd)
