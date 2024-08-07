from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.update import (
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

#
router = APIRouter()


@router.post(
    "/recipes/update",
    status_code=status.HTTP_201_CREATED,
)
@timeout_after()
async def update(
    data: ApiUpdateRecipe,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Update a recipe.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            recipe = await uow.recipes.get(data.recipe_id)
        except EntityNotFoundException:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe {data.recipe_id} not in database.",
            )
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or recipe.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = data.to_domain()
    await bus.handle(cmd)
