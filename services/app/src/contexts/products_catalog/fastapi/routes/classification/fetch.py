from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.brand import (
    ApiBrand,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.category import (
    ApiCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.food_group import (
    ApiFoodGroup,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.parent_category import (
    ApiParentCategory,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.process_type import (
    ApiProcessType,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.source import (
    ApiSource,
)
from src.contexts.products_catalog.shared.domain.enums import ProductClassificationType
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/product-classifications/{classification_type}",
    response_model=list[ApiClassification],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch(
    request: Request,
    classification_type: ProductClassificationType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiClassification]:
    """
    Query for products classifications based on classification type.
    """

    classification_config: dict[
        ProductClassificationType, tuple[str, Type[ApiClassification]]
    ] = {
        ProductClassificationType.CATEGORIES: ("categories", ApiCategory),
        ProductClassificationType.BRANDS: ("brands", ApiBrand),
        ProductClassificationType.FOOD_GROUPS: ("food_groups", ApiFoodGroup),
        ProductClassificationType.PARENT_CATEGORIES: (
            "parent_categories",
            ApiParentCategory,
        ),
        ProductClassificationType.PROCESS_TYPES: ("process_types", ApiProcessType),
        ProductClassificationType.SOURCES: ("sources", ApiSource),
    }

    if classification_type not in classification_config:
        raise HTTPException(
            status_code=404,
            detail=f"classification type {classification_type} not found.",
        )

    uow_repo_name, api_schema_class = classification_config[classification_type]
    return await utils.read_classifications(
        request,
        current_user,
        uow_repo_name,
        api_schema_class,
        bus,
    )
