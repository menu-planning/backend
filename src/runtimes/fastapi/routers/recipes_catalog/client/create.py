"""FastAPI router for client create endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_create_client import (
    ApiCreateClient,
)
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/clients")

@router.post("/")
async def create_client(
    request_body: ApiCreateClient,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Create a new client.
    
    Args:
        request_body: Client creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created client details with client_id
        
    Raises:
        HTTPException: If user lacks permissions or validation fails
    """       
    cmd = request_body.to_domain(current_user.id)
    
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "Client created successfully"},
        status_code=201
    )
