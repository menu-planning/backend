from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.base_tag import (
    ApiTag,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.brand import (
    ApiBrand,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.category import (
    ApiCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.filter import (
    ApiTagFilter,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.food_group import (
    ApiFoodGroup,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.parent_category import (
    ApiParentCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.process_type import (
    ApiProcessType,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.source import (
    ApiSource,
)
from src.contexts.products_catalog.shared.domain.enums import ProductTagType
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type import (
    ApiDietType,
)
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type_filter import (
    ApiDietTypeFilter,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.allergen import (
    ApiAllergen,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.name_tag_filter import (
    ApiNameTagFilter,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/product-tags/allergens",
    response_model=list[ApiAllergen],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_allergen(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiAllergen]:
    """
    Query for products allergens.
    """

    queries = request.query_params
    filters = {k.replace("-", "_"): v for k, v in queries.items()}
    filters["limit"] = int(queries.get("limit", 500))
    filters["sort"] = queries.get("sort", "-name")
    api = ApiNameTagFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        repo = uow.allergens
        try:
            tags = await repo.query(filter=filters)
            return [ApiAllergen.from_domain(i) for i in tags] if tags else []
        except BadRequestException as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/product-tags/diet-types",
    response_model=list[ApiDietType],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_diet_type(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiDietType]:
    """
    Query for products tags based on tag type.
    """

    queries = request.query_params
    filters = {k.replace("-", "_"): v for k, v in queries.items()}
    filters["limit"] = int(queries.get("limit", 500))
    filters["sort"] = queries.get("sort", "-date")
    api = ApiDietTypeFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        repo = uow.diet_types
        try:
            tags = await repo.query(filter=filters)
            return [ApiDietType.from_domain(i) for i in tags] if tags else []
        except BadRequestException as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/product-tags/{tag_type}",
    response_model=list[ApiTag],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch(
    request: Request,
    tag_type: ProductTagType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiDietType]:
    """
    Query for products tags based on tag type.
    """

    tag_config: dict[ProductTagType, tuple[str, Type[ApiTag]]] = {
        ProductTagType.CATEGORIES: ("categories", ApiCategory),
        ProductTagType.BRANDS: ("brands", ApiBrand),
        ProductTagType.FOOD_GROUPS: ("food_groups", ApiFoodGroup),
        ProductTagType.PARENT_CATEGORIES: ("parent_categories", ApiParentCategory),
        ProductTagType.PROCESS_TYPES: ("process_types", ApiProcessType),
        ProductTagType.SOURCES: ("sources", ApiSource),
    }

    if tag_type not in tag_config:
        raise HTTPException(status_code=404, detail=f"Tag type {tag_type} not found.")

    uow_repo_name, api_schema_class = tag_config[tag_type]
    return await utils.read_tags(
        request,
        current_user,
        uow_repo_name,
        api_schema_class,
        bus,
    )
