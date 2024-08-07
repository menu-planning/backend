from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, Path, status
from src.contexts.food_tracker.fastapi import bootstrap
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.domain.commands import DeleteCategory
from src.contexts.recipes_catalog.shared.domain.commands.diet_types.delete import (
    DeleteDietType,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)
from src.contexts.recipes_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.recipes_catalog.shared.domain.enums import RecipeTagType
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/recipes-tags/diet-types/{id}/delete",
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
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
        or tag.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = DeleteDietType(id=id)
    await bus.handle(cmd)


@router.get(
    "/recipe-tags/{tag_type}/{id}/delete",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def delete_tag(
    id: Annotated[int, Path(title="The ID of the tag to delete")],
    tag_type: RecipeTagType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Delete a tag based on tag type.
    """
    tag_config: dict[RecipeTagType, tuple[str, Type[DeleteTag]]] = {
        RecipeTagType.CATEGORY: ("category", DeleteCategory),
        RecipeTagType.MEAL_PLANNING: ("meal_planning", DeleteTag),
    }

    if tag_type not in tag_config:
        raise HTTPException(status_code=400, detail="Invalid tag type provided.")

    repo_name, delete_cmd_class = tag_config[tag_type]
    await utils.delete_tag(
        id,
        current_user,
        repo_name,
        delete_cmd_class,
        bus,
    )
