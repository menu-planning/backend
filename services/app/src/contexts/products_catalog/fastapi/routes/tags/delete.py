from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, Path, status
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.products_catalog.shared.domain.commands import (
    DeleteBrand,
    DeleteCategory,
    DeleteFoodGroup,
    DeleteParentCategory,
    DeleteProcessType,
    DeleteSource,
)
from src.contexts.products_catalog.shared.domain.commands.diet_types.delete import (
    DeleteDietType,
)
from src.contexts.products_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)
from src.contexts.products_catalog.shared.domain.enums import Permission
from src.contexts.products_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.products_catalog.shared.domain.enums import ProductTagType
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/product-tags/diet-types/{id}/delete",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def delete_diet_type(
    id: Annotated[int, Path(title="The ID of the diet type to delete")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Delete a diet type.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        repo = uow.diet_types
        try:
            tag = await repo.get(id)
        except EntityNotFoundException:
            raise HTTPException(status_code=404, detail=f"Tag {id} not in database.")
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or tag.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = DeleteDietType(id=id)
    await bus.handle(cmd)


@router.get(
    "/product-tags/{tag_type}/{id}/delete",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def delete_tag(
    id: Annotated[int, Path(title="The ID of the tag to delete")],
    tag_type: ProductTagType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Delete a tag.
    """
    if current_user.has_permission(Permission.MANAGE_PRODUCTS):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )

    tag_config: dict[ProductTagType, tuple[str, Type[DeleteTag]]] = {
        ProductTagType.CATEGORIES: ("categories", DeleteCategory),
        ProductTagType.BRANDS: ("brands", DeleteBrand),
        ProductTagType.FOOD_GROUPS: ("food_groups", DeleteFoodGroup),
        ProductTagType.PARENT_CATEGORIES: ("parent_categories", DeleteParentCategory),
        ProductTagType.PROCESS_TYPES: ("process_types", DeleteProcessType),
        ProductTagType.SOURCES: ("sources", DeleteSource),
    }

    if tag_type not in tag_config:
        raise HTTPException(status_code=404, detail=f"Tag type {tag_type} not found.")

    uow_repo_name, delete_cmd_class = tag_config[tag_type]
    await utils.delete_tag(
        id,
        current_user,
        uow_repo_name,
        delete_cmd_class,
        bus,
    )
