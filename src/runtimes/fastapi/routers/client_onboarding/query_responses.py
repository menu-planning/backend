"""FastAPI router for single response query endpoint."""

from fastapi import Depends
from typing import Any

from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    ResponseQueryRequest,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.fastapi.dependencies import get_clients_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.client_onboarding.aws_lambda.shared.query_executor import execute_query
from src.contexts.client_onboarding.core.adapters.validators.ownership_validator import FormOwnershipValidator
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/client-onboarding")


@router.post("/query-responses")
async def query_responses(
    request_body: ResponseQueryRequest,
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Execute single response query.
    
    Args:
        request_body: Query request data
        bus: Message bus for business logic
        
    Returns:
        Query results
    """
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        ownership_validator = FormOwnershipValidator()
        result = await execute_query(request_body, uow, ownership_validator)
        await uow.commit()

    return create_success_response(result.model_dump())
