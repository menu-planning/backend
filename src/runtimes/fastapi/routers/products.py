"""FastAPI router for products catalog endpoints."""

from fastapi import Depends, HTTPException, Query
from typing import Any
from pydantic import TypeAdapter

from src.contexts.products_catalog.core.adapters.api_schemas.commands.products.api_add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_filter import (
    ApiClassificationFilter,
)
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import (
    ApiSource,
)
from src.contexts.products_catalog.core.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.core.domain.enums import Permission
from src.contexts.products_catalog.fastapi.dependencies import get_products_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.contexts.shared_kernel.middleware.auth.authentication import AuthContext
from fastapi import Request
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_paginated_response,
    create_router,
)

router = create_router(prefix="/products", tags=["products"])

# Type adapter for JSON serialization (same as Lambda implementation)
ProductListTypeAdapter = TypeAdapter(list[ApiProduct])


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth_context: AuthContext = request.state.auth_context
    if not auth_context.is_authenticated or not auth_context.user_object:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return auth_context.user_object


@router.get("/query")
async def query_products(
    filters: ApiProductFilter = Depends(),
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query products with pagination and filtering.
    
    Uses the same filtering approach as the Lambda implementation.
    FastAPI automatically converts query parameters to ApiProductFilter.
    
    Args:
        filters: Product filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Paginated list of products matching filters
        
    Raises:
        HTTPException: If query parameters are invalid or database error occurs
    """
    try:
        # Convert filters to dict for business logic compatibility
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Query products using bus/UoW pattern (same as Lambda implementation)
        from src.contexts.products_catalog.core.services.uow import UnitOfWork
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result: list = await uow.products.query(filters=filter_dict)
        
        # Convert domain products to API format (same as Lambda implementation)
        api_products = []
        conversion_errors = 0
        
        for product in result:
            try:
                api_product = ApiProduct.from_domain(product)
                api_products.append(api_product)
            except Exception as e:
                conversion_errors += 1
                # Log conversion errors but continue processing
                continue
        
        # Convert to dict format for response (same as Lambda implementation)
        products_data = [product.model_dump() for product in api_products]
        
        # Calculate pagination info
        page = (filter_dict.get("skip", 0) // filter_dict.get("limit", 50)) + 1
        limit = filter_dict.get("limit", 50)
        total = len(products_data)  # This is a limitation of current implementation
        
        return create_paginated_response(
            data=products_data,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query products: {str(e)}")


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single product by ID.
    
    Args:
        product_id: UUID of the product to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Product details
        
    Raises:
        HTTPException: If product not found or invalid ID
    """
    try:
        # Get product using bus/UoW pattern (same as Lambda implementation)
        from src.contexts.products_catalog.core.services.uow import UnitOfWork
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            product = await uow.products.get(product_id)
        
        # Convert domain product to API format (same as Lambda implementation)
        api_product = ApiProduct.from_domain(product)
        product_data = api_product.model_dump()
        return create_success_response(product_data)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Product not found: {str(e)}")


@router.post("/create")
async def create_product(
    request: ApiAddFoodProduct,
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new food product.
    
    Args:
        request: Product creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created product details
        
    Raises:
        HTTPException: If user lacks permissions or validation fails
    """
    try:
        # Check permissions
        if not current_user.has_permission(Permission.MANAGE_PRODUCTS):
            raise HTTPException(
                status_code=403, 
                detail="User does not have enough privileges to manage products"
            )
        
        # Convert API schema to domain command
        cmd = AddFoodProductBulk(add_product_cmds=[request.to_domain()])
        
        # Handle command via message bus
        await bus.handle(cmd)
        
        return create_success_response(
            {"message": "Product created successfully"}, 
            status_code=201
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create product: {str(e)}")


@router.get("/search/similar-names")
async def search_similar_names(
    name: str = Query(..., description="Product name to search for"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Search for products with similar names.
    
    Args:
        name: Product name to search for
        limit: Maximum number of results to return
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        List of products with similar names
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Use bus/UoW pattern for search (same as Lambda implementation)
        from src.contexts.products_catalog.core.services.uow import UnitOfWork
        filter_dict = {"name": name, "limit": limit}
        
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result: list = await uow.products.list_top_similar_names(name)
        
        # Convert domain products to API format (same as Lambda implementation)
        api_products = []
        for product in result:
            try:
                api_product = ApiProduct.from_domain(product)
                api_products.append(api_product)
            except Exception as e:
                # Log conversion errors but continue processing
                continue
        
        # Convert to dict format for response (same as Lambda implementation)
        results_data = [product.model_dump() for product in api_products]
        return create_success_response(results_data)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")


@router.get("/filter-options")
async def get_filter_options(
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get available filter options for products.
    
    Args:
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Available filter options
        
    Raises:
        HTTPException: If filter options retrieval fails
    """
    try:
        # Use bus/UoW pattern for filter options (same as Lambda implementation)
        from src.contexts.products_catalog.core.services.uow import UnitOfWork
        
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            options = await uow.products.get_filter_options()
        
        return create_success_response(options)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get filter options: {str(e)}")


@router.get("/sources")
async def query_product_sources(
    filters: ApiClassificationFilter = Depends(),
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query product sources with pagination and filtering.
    
    Args:
        filters: Source filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Dictionary mapping source IDs to names
        
    Raises:
        HTTPException: If query parameters are invalid or database error occurs
    """
    try:
        # Convert filters to dict for business logic compatibility
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Query sources using bus/UoW pattern (same as Lambda implementation)
        from src.contexts.products_catalog.core.services.uow import UnitOfWork
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result: list = await uow.sources.query(filters=filter_dict)
        
        # Convert domain sources to API format (same as Lambda implementation)
        api_sources = []
        conversion_errors = 0
        
        for source in result:
            try:
                api_source = ApiSource.from_domain(source)
                api_sources.append(api_source)
            except Exception as e:
                conversion_errors += 1
                # Log conversion errors but continue processing
                continue
        
        # Return simplified {id: name} mapping (same as Lambda implementation)
        response_data = {source.id: source.name for source in api_sources}
        return create_success_response(response_data)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query product sources: {str(e)}")


@router.get("/sources/{source_id}")
async def get_product_source(
    source_id: str,
    bus: MessageBus = Depends(get_products_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single product source by ID.
    
    Args:
        source_id: UUID of the source to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Source details as {id: name} mapping
        
    Raises:
        HTTPException: If source not found or invalid ID
    """
    try:
        # Get source using bus/UoW pattern (same as Lambda implementation)
        from src.contexts.products_catalog.core.services.uow import UnitOfWork
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            source = await uow.sources.get(source_id)
        
        # Convert domain source to API format (same as Lambda implementation)
        api_source = ApiSource.from_domain(source)
        response_data = {api_source.id: api_source.name}
        return create_success_response(response_data)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {str(e)}")
