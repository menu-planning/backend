from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from src.contexts.recipes_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.recipes_catalog.fastapi.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.category import (
    ApiCategory,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.meal_planning import (
    ApiMealPlanning,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type import (
    ApiDietType,
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
    "/recipe-tags/categories/{id}",
    response_model=ApiCategory,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_category_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiCategory:
    """
    Retrieve specific category.
    """
    return await utils.read_tag(id, current_user, "categories", ApiCategory, bus)


@router.get(
    "/recipe-tags/meal-plannings/{id}",
    response_model=ApiMealPlanning,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_meal_planning_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiMealPlanning:
    """
    Retrieve specific meal planning.
    """
    return await utils.read_tag(
        id, current_user, "meal_plannings", ApiMealPlanning, bus
    )


@router.get(
    "/recipe-tags/diet-types/{id}",
    response_model=ApiDietType,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_diet_type_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiDietType:
    """
    Retrieve specific diet types.
    """
    return await utils.read_tag(id, current_user, "diet_types", ApiDietType, bus)


@router.get(
    "/recipe-tags/flavors/{id}",
    response_model=ApiFlavor,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_flavor_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiFlavor:
    """
    Retrieve specific flavor.
    """
    return await utils.read_name_tag(id, current_user, "flavors", ApiFlavor, bus)


@router.get(
    "/recipe-tags/cuisines/{id}",
    response_model=ApiCuisine,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_flavor_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiCuisine:
    """
    Retrieve specific cuisine.
    """
    return await utils.read_name_tag(id, current_user, "cuisines", ApiCuisine, bus)


@router.get(
    "/recipe-tags/textures/{id}",
    response_model=ApiTexture,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_texture_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiTexture:
    """
    Retrieve specific texture.
    """
    return await utils.read_name_tag(id, current_user, "textures", ApiTexture)


@router.get(
    "/recipe-tags/allergens/{id}",
    response_model=ApiAllergen,
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def get_allergen_by_id(
    id: Annotated[int, Path(title="The ID of the tag to fetch")],
    current_user: Annotated[SeedUser, Depends(IAMProvider.current_active_user)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> ApiAllergen:
    """
    Retrieve specific allergen.
    """
    return await utils.read_name_tag(id, current_user, "allergens", ApiAllergen)
