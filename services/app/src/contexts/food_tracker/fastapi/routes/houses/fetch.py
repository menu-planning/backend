from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.get(
    "/houses",
    response_model=list[ApiHouse],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def read_houses(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiHouse]:
    """
    Query for houses.
    """
    queries = request.query_params
    if not (
        current_user.has_permission(Permission.MANAGE_HOUSES)
        or current_user.id == queries.get("owner")
        or current_user.id in (queries.get("members") or [])
        or current_user.id in (queries.get("nutritionists") or [])
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    valid_filter = {}
    valid_filter = {k.replace("-", "_"): v for k, v in queries.items()}
    valid_filter["limit"] = int(queries.get("limit", 500))
    valid_filter["sort"] = queries.get("sort", "-created_at")
    uow: UnitOfWork
    with bus.uow as uow:
        result = uow.houses.query(filter=valid_filter)
    result = [ApiHouse.from_domain(house) for house in result]
