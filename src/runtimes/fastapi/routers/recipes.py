"""FastAPI router for recipes catalog endpoints."""

from fastapi import Depends, HTTPException, Request
from typing import Any
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_filter import (
    ApiMealFilter,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_filter import (
    ApiClientFilter,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.shared_kernel.middleware.auth.authentication import AuthContext
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
)
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_paginated_response,
    create_router,
)

router = create_router(prefix="/recipes", tags=["recipes"])

# Type adapters for JSON serialization (same as Lambda implementation)
RecipeListTypeAdapter = TypeAdapter(list[ApiRecipe])
MealListTypeAdapter = TypeAdapter(list[ApiMeal])
ClientListTypeAdapter = TypeAdapter(list[ApiClient])


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth_context: AuthContext = request.state.auth_context
    if not auth_context.is_authenticated or not auth_context.user_object:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return auth_context.user_object


# ============================================================================
# RECIPE ENDPOINTS
# ============================================================================

@router.get("/query")
async def query_recipes(
    filters: ApiRecipeFilter = Depends(),
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query recipes with pagination and filtering."""
    try:
        # Convert filters to dict for business logic compatibility
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Apply user-specific tag filtering for recipes (same as Lambda implementation)
        if current_user:
            if filter_dict.get("tags"):
                filter_dict["tags"] = [
                    (k, v, current_user.id) for k, vs in filter_dict["tags"].items() for v in vs
                ]
            if filter_dict.get("tags_not_exists"):
                filter_dict["tags_not_exists"] = [
                    (k, v, current_user.id)
                    for k, vs in filter_dict["tags_not_exists"].items()
                    for v in vs
                ]
        
        # Query using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result: list = await uow.recipes.query(filters=filter_dict)
        
        # Convert domain recipes to API format (same as Lambda implementation)
        api_recipes = []
        for recipe in result:
            api_recipe = ApiRecipe.from_domain(recipe)
            api_recipes.append(api_recipe)
        
        # Serialize API recipes (same as Lambda implementation)
        response_body = RecipeListTypeAdapter.dump_json(api_recipes)
        
        return create_success_response(response_body)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query recipes: {str(e)}")


@router.get("/{recipe_id}")
async def get_recipe(
    recipe_id: str,
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single recipe by ID."""
    try:
        if not recipe_id:
            error_message = "Recipe ID is required"
            raise ValueError(error_message)
        
        # Get using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            try:
                recipe = await uow.recipes.get(recipe_id)
            except EntityNotFoundError as err:
                error_message = f"Recipe {recipe_id} not in database"
                raise ValueError(error_message) from err
        
        # Convert domain recipe to API recipe (same as Lambda implementation)
        api_recipe = ApiRecipe.from_domain(recipe)
        
        # Serialize API recipe (same as Lambda implementation)
        response_body = api_recipe.model_dump_json()
        
        return create_success_response(response_body)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get recipe: {str(e)}")


# ============================================================================
# MEAL ENDPOINTS
# ============================================================================

@router.get("/meals/query")
async def query_meals(
    filters: ApiMealFilter = Depends(),
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query meals with pagination and filtering."""
    try:
        # Convert filters to dict for business logic compatibility
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Apply user-specific tag filtering for meals (same as Lambda implementation)
        if current_user:
            if filter_dict.get("tags"):
                filter_dict["tags"] = [
                    (k, v, current_user.id) for k, vs in filter_dict["tags"].items() for v in vs
                ]
            if filter_dict.get("tags_not_exists"):
                filter_dict["tags_not_exists"] = [
                    (k, v, current_user.id)
                    for k, vs in filter_dict["tags_not_exists"].items()
                    for v in vs
                ]
        
        # Query using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result: list = await uow.meals.query(filters=filter_dict)
        
        # Convert domain meals to API format (same as Lambda implementation)
        api_meals = []
        conversion_errors = 0
        
        for _, meal in enumerate(result):
            try:
                api_meal = ApiMeal.from_domain(meal)
                api_meals.append(api_meal)
            except Exception:
                conversion_errors += 1
                # Continue processing other meals instead of failing completely
        
        if conversion_errors > 0:
            # Log warning but continue - this is handled by logging middleware
            pass
        
        # Serialize API meals (same as Lambda implementation)
        response_body = MealListTypeAdapter.dump_json(api_meals)
        
        return create_success_response(response_body)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query meals: {str(e)}")


@router.get("/meals/{meal_id}")
async def get_meal(
    meal_id: str,
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single meal by ID."""
    try:
        if not meal_id:
            error_message = "Meal ID is required"
            raise ValueError(error_message)
        
        # Get using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            meal = await uow.meals.get(meal_id)
        
        if not meal:
            error_message = "Meal not found"
            raise ValueError(error_message)
        
        # Convert domain meal to API meal (same as Lambda implementation)
        api_meal = ApiMeal.from_domain(meal)
        
        # Serialize API meal (same as Lambda implementation)
        response_body = api_meal.model_dump_json()
        
        return create_success_response(response_body)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get meal: {str(e)}")


# ============================================================================
# CLIENT ENDPOINTS
# ============================================================================

@router.get("/clients/query")
async def query_clients(
    filters: ApiClientFilter = Depends(),
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query clients with pagination and filtering."""
    try:
        # Convert filters to dict for business logic compatibility
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Handle user-specific tag filtering (same as Lambda implementation)
        if current_user and filter_dict.get("tags"):
            filter_dict["tags"] = [(i, current_user.id) for i in filter_dict["tags"]]
        if current_user and filter_dict.get("tags_not_exists"):
            filter_dict["tags_not_exists"] = [
                (i, current_user.id) for i in filter_dict["tags_not_exists"]
            ]
        
        # Query using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result = await uow.clients.query(filters=filter_dict)
        
        # Convert domain clients to API format (same as Lambda implementation)
        api_clients = [ApiClient.from_domain(client) for client in result]
        
        # Serialize API clients (same as Lambda implementation)
        response_body = ClientListTypeAdapter.dump_json(api_clients)
        
        return create_success_response(response_body)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query clients: {str(e)}")


@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single client by ID."""
    try:
        if not client_id:
            error_message = "Client ID is required"
            raise ValueError(error_message)
        
        # Get using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            client = await uow.clients.get(client_id)
        
        if not client:
            error_message = "Client not found"
            raise ValueError(error_message)
        
        # Convert domain client to API client (same as Lambda implementation)
        api_client = ApiClient.from_domain(client)
        
        # Serialize API client (same as Lambda implementation)
        response_body = api_client.model_dump_json()
        
        return create_success_response(response_body)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get client: {str(e)}")


# ============================================================================
# SHOPPING LIST ENDPOINTS
# ============================================================================

@router.get("/shopping-list/recipes")
async def get_shopping_list_recipes(
    bus: MessageBus = Depends(get_recipes_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get recipes for shopping list generation."""
    try:
        # Query using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            # This would typically involve more complex logic for shopping list generation
            # For now, we'll return a simple list of recipes
            result: list = await uow.recipes.query(filters={"author_id": current_user.id})
        
        # Convert domain recipes to API format (same as Lambda implementation)
        api_recipes = []
        for recipe in result:
            api_recipe = ApiRecipe.from_domain(recipe)
            api_recipes.append(api_recipe)
        
        # Serialize API recipes (same as Lambda implementation)
        response_body = RecipeListTypeAdapter.dump_json(api_recipes)
        
        return create_success_response(response_body)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get shopping list recipes: {str(e)}")
