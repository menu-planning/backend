from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipe.rate import (
    ApiRateRecipe,
)
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
    "/recipes/rate",
    status_code=status.HTTP_201_CREATED,
)
@timeout_after()
async def rate(
    rate_recipe: ApiRateRecipe,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Rate a recipe.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            await uow.recipes.get(rate_recipe.rating.recipe_id)
        except EntityNotFoundException:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe {rate_recipe.rating.recipe_id} not in database.",
            )
    cmd = rate_recipe.to_domain()
    await bus.handle(cmd)
