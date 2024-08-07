from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.diet_types.create import (
    ApiCreateDietType,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.category.create import (
    ApiCreateCategory,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.create import (
    ApiCreateTag,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.meal_planning import (
    ApiMealPlanning,
)
from src.contexts.recipes_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.recipes_catalog.shared.domain.enums import RecipeTagType
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.post("/recipe-tags/diet-type", status_code=status.HTTP_201_CREATED)
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
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
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


@router.post("/recipe-tags/{tag_type}", status_code=status.HTTP_201_CREATED)
@timeout_after()
async def create_tag(
    tag_data: ApiCreateTag,
    tag_type: RecipeTagType,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new tag based on tag type.
    """
    tag_config: dict[RecipeTagType, Type[ApiCreateTag]] = {
        RecipeTagType.CATEGORY: ApiCreateCategory,
        RecipeTagType.MEAL_PLANNING: ApiMealPlanning,
    }

    if tag_type not in tag_config:
        raise HTTPException(status_code=400, detail="Invalid tag type provided.")

    api_class = tag_config[tag_type]
    tag_data = api_class(**tag_data.model_dump())
    await utils.create_tag(
        tag_data,
        current_user,
        bus,
    )
