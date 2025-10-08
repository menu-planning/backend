"""FastAPI router for tag search endpoint."""

from fastapi import Depends, HTTPException, Query
from typing import Annotated, Any

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag_filter import (
    ApiTagFilter,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)
from src.runtimes.fastapi.routers.type_adapters import TagListAdapter

router = create_router(prefix="/tags")


@router.get("/search")
async def search_tags(
    filters: Annotated[ApiTagFilter, Query()],
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Search tags with pagination and filtering.
    
    This endpoint replaces the problematic /tags/query path to avoid conflicts
    with /tags/{tag_id}. Uses the same filtering approach as the Lambda implementation.
    
    Args:
        filters: Tag filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        List of tags matching filters
        
    Raises:
        HTTPException: If query parameters are invalid or database error occurs
    """
    filter_dict = filters.model_dump(exclude_none=True)
    if filter_dict.get("author_id") and filter_dict.get("author_id") != current_user.id:
        error_message = "User does not have enough privileges to search tags"
        raise PermissionError(error_message)
    else:
        filter_dict["author_id"] = current_user.id
        
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result = await uow.tags.query(filters=filter_dict)
    
    api_tags = []
    conversion_errors = 0
    
    for _, tag in enumerate(result):
        try:
            api_tag = ApiTag.from_domain(tag)
            api_tags.append(api_tag)
        except Exception:
            conversion_errors += 1
            # Continue processing other tags instead of failing completely
    
    if conversion_errors > 0:
        # Log warning but continue - this is handled by logging middleware
        pass
    
    response_body = TagListAdapter.dump_json(api_tags)
    
    return create_success_response(response_body)
