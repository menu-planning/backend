from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.category import (
    ApiCategory,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.meal_planning import (
    ApiMealPlanning,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type import (
    ApiDietType,
)
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type_filter import (
    ApiDietTypeFilter,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.allergen import (
    ApiAllergen,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.cuisine import (
    ApiCuisine,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.flavor import (
    ApiFlavor,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.texture import (
    ApiTexture,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus

from . import utils

router = APIRouter()


@router.get(
    "/recipe-tags/categories",
    response_model=list[ApiCategory],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_categories(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiCategory]:
    """
    Query for categories.
    """
    return await utils.read_tags(
        request,
        current_user,
        "categories",
        ApiCategory,
        bus,
    )


@router.get(
    "/recipe-tags/meal-plannings",
    response_model=list[ApiMealPlanning],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_meal_plannings(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiMealPlanning]:
    """
    Query for meal plannings.
    """
    return await utils.read_tags(
        request=request,
        current_user=current_user,
        uow_repo_name="meal_plannings",
        bus=bus,
        api_schema_class=ApiMealPlanning,
    )


@router.get(
    "/recipe-tags/diet-types",
    response_model=list[ApiDietType],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_diet_types(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiDietType]:
    """
    Query for recipes diet type.
    """
    return await utils.read_tags(
        request=request,
        current_user=current_user,
        uow_repo_name="diet_types",
        bus=bus,
        api_schema_class=ApiDietType,
        api_filter_class=ApiDietTypeFilter,
    )


@router.get(
    "/recipe-tags/allergens",
    response_model=list[ApiAllergen],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_allergens(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiAllergen]:
    """
    Query for allergens.
    """
    return await utils.read_name_tags(
        request,
        current_user,
        "allergens",
        ApiAllergen,
        bus,
    )


@router.get(
    "/recipe-tags/flavors",
    response_model=list[ApiFlavor],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_flavors(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiFlavor]:
    """
    Query for flavors.
    """
    return await utils.read_name_tags(
        request,
        current_user,
        "flavors",
        ApiFlavor,
        bus,
    )


@router.get(
    "/recipe-tags/cuisines",
    response_model=list[ApiCuisine],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_cuisines(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiCuisine]:
    """
    Query for cuisines.
    """
    return await utils.read_name_tags(
        request, current_user, "cuisines", ApiCuisine, bus
    )


@router.get(
    "/recipe-tags/textures",
    response_model=list[ApiTexture],
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def fetch_textures(
    request: Request,
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> list[ApiTexture]:
    """
    Query for textures.
    """
    return await utils.read_name_tags(
        request,
        current_user,
        "textures",
        ApiTexture,
        bus,
    )
