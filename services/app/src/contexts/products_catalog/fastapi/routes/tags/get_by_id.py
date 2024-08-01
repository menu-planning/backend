from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, Path, status
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
from src.contexts.products_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.products_catalog.shared.domain.enums import ProductTagType
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type import (
    ApiDietType,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.allergen import (
    ApiAllergen,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/product-tags/allergens/{id}",
    response_model=ApiAllergen,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_allergen_by_id(
    id: Annotated[int, Path(title="The ID of the allergen to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiAllergen:
    """
    Retrieve specific tag by type.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            tag = await uow.allergens.get(id)
        except EntityNotFoundException:
            raise HTTPException(status_code=404, detail=f"Tag {id} not in database.")
    if not (current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    return ApiAllergen.from_domain(tag)


@router.get(
    "/product-tags/diet-types/{id}",
    response_model=ApiDietType,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_diet_type_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiDietType:
    """
    Retrieve specific tag by type.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            diet_type = await uow.diet_types.get(id)
        except EntityNotFoundException:
            raise HTTPException(status_code=404, detail=f"Tag {id} not in database.")
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or diet_type.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    return ApiDietType.from_domain(diet_type)


@router.get(
    "/product-tags/{tag_type}/{id}",
    response_model=ApiTag,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    tag_type: ProductTagType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiDietType:
    """
    Retrieve specific tag by type.
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
    return await utils.read_tag(
        id,
        current_user,
        uow_repo_name,
        api_schema_class,
        bus,
    )
