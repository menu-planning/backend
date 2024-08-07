from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

#
router = APIRouter()


@router.get(
    "/recipes",
    response_model=list[ApiRecipe],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiRecipe]:
    """
    Query for recipes.
    """
    queries = request.query_params
    filters = {k.replace("-", "_"): v for k, v in queries.items()}
    filters["limit"] = int(queries.get("limit", 500))
    filters["sort"] = queries.get("sort", "-created_at")
    api = ApiRecipeFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            if current_user.has_permission(Permission.MANAGE_RECIPES):
                recipes = await uow.recipes.query(filter=filters)
                return [ApiRecipe.from_domain(i) for i in recipes] if recipes else []
            else:
                if filters.get("author_id") is not None:
                    if filters.get("author_id") != current_user.id:
                        # only admin or the author can query for their own recipes
                        logger.error(
                            f"User {current_user.id} is not admnin and is trying "
                            f"to query for recipes from user {filters.get('author_id')}"
                        )
                        raise HTTPException(
                            status_code=403,
                            detail="User does not have enough privilegies.",
                        )
                    recipes = await uow.recipes.query(filter=filters)
                else:
                    # query for all private recipes owned by the user
                    own_recipes = await uow.recipes.query(
                        filter=filters
                        | {"author_id": current_user.id}
                        | {"privacy": Privacy.PRIVATE}
                    )
                    # query for all public recipes
                    public_recipes = await uow.recipes.query(
                        filter=filters | {"privacy": Privacy.PUBLIC}
                    )
                    recipes = own_recipes + public_recipes
                return [ApiRecipe.from_domain(i) for i in recipes] if recipes else []
        except BadRequestException as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=str(e))
