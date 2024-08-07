from typing import Annotated

from fastapi import APIRouter, Depends, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.house import (
    ApiHouse,
)
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.get(
    "/houses/nutritionist-of",
    response_model=list[ApiHouse],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def read_houses_user_is_nutritionist(
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiHouse]:
    """
    Retrieve houses the user is nutritionist of.
    """
    uow: UnitOfWork
    with bus.uow as uow:
        houses_user_is_nutritionist = await uow.houses.query(
            filter={"nutritionists": current_user.id}
        )
    return [ApiHouse.from_domain(house) for house in houses_user_is_nutritionist]
