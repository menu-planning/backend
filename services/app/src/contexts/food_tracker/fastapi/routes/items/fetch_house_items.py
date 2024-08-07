from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.item import ApiItem
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
    "/food-items/houses/{house_id}",
    response_model=list[ApiItem],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_house_items(
    house_id: Annotated[int, Path(title="The ID of the house to get items from")],
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiItem]:
    """
    Query for food items on a house.
    """
    uow: UnitOfWork
    with bus.uow as uow:
        if isinstance(house_id, str):
            house_id = [house_id]
        for id in house_id:
            house = await uow.houses.get(id)
            if not (
                current_user.has_permission(Permission.MANAGE_HOUSES)
                or current_user.id == house.owner_id
                or current_user.id in house.members_ids
                or current_user.id in house.nutritionists_ids
            ):
                raise ForbiddenException()
    queries = request.query_params
    valid_filter = {}
    valid_filter = {k.replace("-", "_"): v for k, v in queries.items()}
    valid_filter["limit"] = int(queries.get("limit", 500))
    valid_filter["sort"] = queries.get("sort", "-date")
    uow: UnitOfWork
    with bus.uow as uow:
        items = uow.items.query(filter=valid_filter)
    return [ApiItem.from_domain(item) for item in items]
