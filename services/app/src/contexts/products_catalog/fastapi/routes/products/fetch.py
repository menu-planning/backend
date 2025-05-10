from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


@router.get(
    "/products",
    response_model=list[ApiProduct],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiProduct]:
    """
    Query for products.
    """
    queries = request.query_params
    filters = {k.replace("-", "_"): v for k, v in queries.items()}
    filters["limit"] = int(queries.get("limit", 500))
    filters["sort"] = queries.get("sort", "-updated_at")
    api = ApiProductFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            result = await uow.products.query(filter=filters)
        except BadRequestException as e:
            raise HTTPException(status_code=400, detail=str(e))
    return [ApiProduct.from_domain(i) for i in result] if result else []
