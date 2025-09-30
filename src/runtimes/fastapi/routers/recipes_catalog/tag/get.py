"""FastAPI router for tag get endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/tags", tags=["tags"])

@router.get("/{tag_id}")
async def get_tag(
    tag_id: str,
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Get a single tag by ID.
    
    Args:
        tag_id: UUID of the tag to retrieve
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Tag details
        
    Raises:
        HTTPException: If tag not found or invalid ID
    """
    if not tag_id:
        error_message = "Tag ID is required"
        raise ValueError(error_message)
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        tag = await uow.tags.get(tag_id)
    
    api_tag = ApiTag.from_domain(tag)
    
    response_body = api_tag.model_dump_json()
    
    return create_success_response(response_body)
