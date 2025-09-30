"""FastAPI router for product create endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.products_catalog.core.adapters.api_schemas.commands.products.api_add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.core.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.core.domain.enums import Permission
from src.contexts.products_catalog.fastapi.dependencies import get_products_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_products_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/products", tags=["products"])


@router.post("/")
async def create_product(
    request: ApiAddFoodProduct,
    current_user: Annotated[Any, Depends(get_products_user)],
    bus: MessageBus = Depends(get_products_bus),
) -> Any:
    """Create a new food product.
    
    Args:
        request: Product creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created product details
    """
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
