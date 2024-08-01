from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.products.add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.post("/products", status_code=status.HTTP_201_CREATED)
@timeout_after()
async def create(
    data: ApiAddFoodProduct,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new food product.
    """
    if current_user.has_permission(Permission.MANAGE_PRODUCTS):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = data.to_domain()
    try:
        await bus.handle(cmd)
    except BadRequestException as e:
        raise HTTPException(status_code=409, detail=str(e))
