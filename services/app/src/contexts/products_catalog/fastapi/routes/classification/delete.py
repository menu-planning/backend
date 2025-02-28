from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, Path, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.domain.commands.classifications.base_classes import (
    DeleteClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.brand.delete import (
    DeleteBrand,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.category.delete import (
    DeleteCategory,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.food_group.delete import (
    DeleteFoodGroup,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.parent_category.delete import (
    DeleteParentCategory,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.process_type.delete import (
    DeleteProcessType,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.source.delete import (
    DeleteSource,
)
from src.contexts.products_catalog.shared.domain.enums import Permission
from src.contexts.products_catalog.shared.domain.enums import ProductClassificationType
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/product-classifications/{classification_type}/{id}/delete",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def delete_classification(
    id: Annotated[int, Path(title="The ID of the classification to delete")],
    classification_type: ProductClassificationType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Delete a classification.
    """
    if current_user.has_permission(Permission.MANAGE_PRODUCTS):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )

    classification_config: dict[
        ProductClassificationType, tuple[str, Type[DeleteClassification]]
    ] = {
        ProductClassificationType.CATEGORIES: ("categories", DeleteCategory),
        ProductClassificationType.BRANDS: ("brands", DeleteBrand),
        ProductClassificationType.FOOD_GROUPS: ("food_groups", DeleteFoodGroup),
        ProductClassificationType.PARENT_CATEGORIES: (
            "parent_categories",
            DeleteParentCategory,
        ),
        ProductClassificationType.PROCESS_TYPES: ("process_types", DeleteProcessType),
        ProductClassificationType.SOURCES: ("sources", DeleteSource),
    }

    if classification_type not in classification_config:
        raise HTTPException(
            status_code=404,
            detail=f"classification type {classification_type} not found.",
        )

    uow_repo_name, delete_cmd_class = classification_config[classification_type]
    await utils.delete_classification(
        id,
        current_user,
        uow_repo_name,
        delete_cmd_class,
        bus,
    )
