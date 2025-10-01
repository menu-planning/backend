"""FastAPI router for user creation endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.iam.core.adapters.api_schemas.commands.api_create_user import (
    ApiCreateUser,
)
from src.contexts.iam.core.domain.root_aggregate.user import User as IAMUser
from src.contexts.iam.fastapi.dependencies import get_iam_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_iam_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/users")

@router.post("/")
async def create_user(
    request_body: ApiCreateUser,
    current_user: Annotated[IAMUser, Depends(get_iam_user)],
    bus: MessageBus = Depends(get_iam_bus),
) -> Any:
    """Create a new user.
    
    Args:
        request_body: User creation data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Created user details with user_id
        
    Raises:
        HTTPException: If user creation fails or validation fails
    """
    # Convert to domain command
    cmd = request_body.to_domain()
    
    # Handle the command through the message bus
    await bus.handle(cmd)
    
    return create_success_response(
        {"message": "User created successfully"},
        status_code=201
    )
