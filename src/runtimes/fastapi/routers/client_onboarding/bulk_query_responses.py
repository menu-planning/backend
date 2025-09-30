"""FastAPI router for bulk response queries endpoint."""

from fastapi import Depends
from typing import Any

from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    BulkResponseQueryRequest,
    ResponseQueryResponse,
    BulkResponseQueryResponse,
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

router = create_router(prefix="/client-onboarding", tags=["client-onboarding"])


@router.post("/bulk-query-responses")
async def bulk_query_responses(
    request_body: BulkResponseQueryRequest,
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Execute multiple response queries.
    
    Args:
        request_body: Bulk query request data
        bus: Message bus for business logic
        
    Returns:
        Bulk query results
    """
    results = []
    errors = []
    successful_queries = 0

    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        ownership_validator = FormOwnershipValidator()

        for query in request_body.queries:
            try:
                result = await execute_query(query, uow, ownership_validator)
                results.append(result)
                if result.success:
                    successful_queries += 1
            except Exception as e:
                results.append(
                    ResponseQueryResponse(
                        success=False,
                        query_type=query.query_type,
                        total_count=0,
                        returned_count=0,
                        forms=None,
                        responses=None,
                        pagination=None,
                    )
                )
                errors.append(f"Query {len(results)} failed: {e!s}")

        await uow.commit()

    # Create bulk response
    bulk_response = BulkResponseQueryResponse(
        success=successful_queries == len(request_body.queries),
        total_queries=len(request_body.queries),
        successful_queries=successful_queries,
        results=results,
        errors=errors if errors else None,
    )

    return create_success_response(bulk_response.model_dump())
