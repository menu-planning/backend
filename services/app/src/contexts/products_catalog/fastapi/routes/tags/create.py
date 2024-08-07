from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.diet_types.create import (
    ApiCreateDietType,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.base_class import (
    ApiCreateTag,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.brand.create import (
    ApiCreateBrand,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.category.create import (
    ApiCreateCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.food_group.create import (
    ApiCreateFoodGroup,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.parent_category.create import (
    ApiCreateParentCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.process_type.create import (
    ApiCreateProcessType,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.source.create import (
    ApiCreateSource,
)
from src.contexts.products_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.products_catalog.shared.domain.enums import ProductTagType
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.post("/product-tags/diet-type", status_code=status.HTTP_201_CREATED)
@timeout_after()
async def create_diet_type(
    data: ApiCreateDietType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new diet type.
    """
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or current_user.id == data.author_id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = data.to_domain()

    try:
        await bus.handle(cmd)
    except BadRequestException as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/product-tags/{tag_type}", status_code=status.HTTP_201_CREATED)
@timeout_after()
async def create_tag(
    data: ApiCreateTag,
    tag_type: ProductTagType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new tag based on tag type.
    """
    tag_config: dict[ProductTagType, Type[ApiCreateTag]] = {
        ProductTagType.CATEGORIES: ApiCreateCategory,
        ProductTagType.BRANDS: ApiCreateBrand,
        ProductTagType.FOOD_GROUPS: ApiCreateFoodGroup,
        ProductTagType.PARENT_CATEGORIES: ApiCreateParentCategory,
        ProductTagType.PROCESS_TYPES: ApiCreateProcessType,
        ProductTagType.SOURCES: ApiCreateSource,
    }
    if tag_type not in ProductTagType:
        raise HTTPException(status_code=404, detail=f"Tag type {tag_type} not found.")

    api_class = tag_config[tag_type]
    data = api_class(**data.model_dump())
    await utils.create_tag(data, current_user, bus)
