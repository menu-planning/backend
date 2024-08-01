from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.commands.items.commands_api_schema import (
    ApiUpdateItem,
)
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.item import ApiItem
from src.contexts.food_tracker.shared.domain.enums import Permission
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.exceptions import ForbiddenException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.patch(
    "/food-items/{item_id}/update",
    response_model=ApiItem,
    status_code=status.HTTP_200_OK,
)
async def update(
    item_id: Annotated[int, Path(title="The ID of the item to update")],
    api: ApiUpdateItem,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> None:
    """
    Update an item.
    """
    uow: UnitOfWork
    with bus.uow as uow:
        item = await uow.items.get(item_id)
        house = await uow.houses.get(item.house_id)
    if not (
        current_user.has_permission(Permission.MANAGE_ITEMS)
        or current_user.id == house.owner_id
        or current_user.id in house.members_ids
        or current_user.id in house.nutritionists_ids
    ):
        raise ForbiddenException()
    cmd = api.to_domain(item_id=item_id)
    await bus.handle(cmd)
