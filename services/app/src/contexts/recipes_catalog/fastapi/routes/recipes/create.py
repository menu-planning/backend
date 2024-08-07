from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.create import (
    ApiCreateRecipe,
)
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

#
router = APIRouter()


@router.post("/recipes", status_code=status.HTTP_201_CREATED)
@timeout_after()
async def create(
    data: ApiCreateRecipe,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new recipe.
    """
    if data.author_id and not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or current_user.id == data.author_id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    else:
        data.author_id = current_user.id
    cmd = data.to_domain()

    await bus.handle(cmd)
