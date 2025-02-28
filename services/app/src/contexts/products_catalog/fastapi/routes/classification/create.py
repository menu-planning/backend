from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.base_class import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.brand.create import (
    ApiCreateBrand,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.category.create import (
    ApiCreateCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.food_group.create import (
    ApiCreateFoodGroup,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.parent_category.create import (
    ApiCreateParentCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.process_type.create import (
    ApiCreateProcessType,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.source.create import (
    ApiCreateSource,
)
from src.contexts.products_catalog.shared.domain.enums import ProductClassificationType
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.post(
    "/product-classifications/{classification_type}",
    status_code=status.HTTP_201_CREATED,
)
@timeout_after()
async def create_classification(
    data: ApiCreateClassification,
    classification_type: ProductClassificationType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new classification based on classification type.
    """
    classification_config: dict[
        ProductClassificationType, Type[ApiCreateClassification]
    ] = {
        ProductClassificationType.CATEGORIES: ApiCreateCategory,
        ProductClassificationType.BRANDS: ApiCreateBrand,
        ProductClassificationType.FOOD_GROUPS: ApiCreateFoodGroup,
        ProductClassificationType.PARENT_CATEGORIES: ApiCreateParentCategory,
        ProductClassificationType.PROCESS_TYPES: ApiCreateProcessType,
        ProductClassificationType.SOURCES: ApiCreateSource,
    }
    if classification_type not in ProductClassificationType:
        raise HTTPException(
            status_code=404,
            detail=f"Classification type {classification_type} not found.",
        )

    api_class = classification_config[classification_type]
    data = api_class(**data.model_dump())
    await utils.create_classification(data, current_user, bus)
