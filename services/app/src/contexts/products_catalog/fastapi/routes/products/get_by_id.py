from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.get(
    "/products/{id}",
    response_model=ApiProduct,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_by_id(
    id: Annotated[str, Path(title="The ID of the product to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiProduct:
    """
    Retrieve specific product by id.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            product = await uow.products.get(id)
        except EntityNotFoundException:
            raise HTTPException(
                status_code=404, detail=f"product {id} not in database."
            )
    return ApiProduct.from_domain(product)
