from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.services.messagebus import MessageBus

#
router = APIRouter()


@router.get(
    "/recipes/{id}",
    response_model=ApiRecipe,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_by_id(
    id: Annotated[int, Path(title="The ID of the recipe to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiRecipe:
    """
    Retrieve specific recipe.
    """

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            recipe = await uow.recipes.get(id)
        except EntityNotFoundException:
            raise HTTPException(status_code=404, detail=f"Recipe {id} not in database.")
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or recipe.author_id == current_user.id
        or recipe.privacy == Privacy.PUBLIC
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    return ApiRecipe.from_domain(recipe)
