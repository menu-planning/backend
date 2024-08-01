from typing import Annotated

from fastapi import APIRouter, Depends, status
from src.contexts.food_tracker.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.food_tracker.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.food_tracker.shared.adapters.api_schemas.commands.houses.commands_api_schema import (
    ApiCreateHouse,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.post("/houses/create", status_code=status.HTTP_201_CREATED)
async def create_house(
    name: str,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new house.
    """
    cmd = ApiCreateHouse(owner_id=current_user.id, name=name).to_domain()
    await bus.handle(cmd)
