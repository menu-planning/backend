"""FastAPI router for client onboarding endpoints."""

from fastapi import Depends, HTTPException, Request
from typing import Any

from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_setup_onboarding_form import (
    ApiSetupOnboardingForm,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_update_webhook_url import (
    ApiUpdateWebhookUrl,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_delete_onboarding_form import (
    ApiDeleteOnboardingForm,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_process_webhook import (
    ApiProcessWebhook,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    ResponseQueryRequest,
    BulkResponseQueryRequest,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_management import (
    FormManagementResponse,
    FormOperationType,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.fastapi.dependencies import get_clients_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.client_onboarding.core.domain.shared.value_objects.user import User
from src.contexts.shared_kernel.middleware.auth.authentication import AuthContext
from src.contexts.client_onboarding.aws_lambda.shared.query_executor import execute_query
from src.contexts.client_onboarding.core.adapters.validators.ownership_validator import FormOwnershipValidator
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)
from datetime import datetime, UTC
import json

router = create_router(prefix="/client-onboarding", tags=["client-onboarding"])


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth_context: AuthContext = request.state.auth_context
    if not auth_context.is_authenticated or not auth_context.user_object:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return auth_context.user_object


# Forms endpoints

@router.post("/forms")
async def create_form(
    request_body: ApiSetupOnboardingForm,
    bus: MessageBus = Depends(get_clients_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create new onboarding form."""
    try:
        # Execute business logic using MessageBus (same as Lambda implementation)
        cmd = request_body.to_domain(user_id=current_user.id)
        await bus.handle(cmd)

        return create_success_response(
            {
                "message": "Form setup initiated successfully",
                "details": {
                    "form_type": request_body.typeform_id,
                    "user_id": str(current_user.id),
                },
            },
            status_code=201
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create form: {str(e)}")


@router.patch("/forms/{form_id}")
async def update_form(
    form_id: int,
    request_body: ApiUpdateWebhookUrl,
    bus: MessageBus = Depends(get_clients_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update existing onboarding form."""
    try:
        # Ensure path form_id overrides body form_id (same as Lambda implementation)
        api_cmd = ApiUpdateWebhookUrl(
            form_id=form_id, 
            new_webhook_url=request_body.new_webhook_url
        )

        # Business logic: Update form through UoW (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            # Get existing form and verify ownership
            existing_form = await uow.onboarding_forms.get_by_id(form_id)
            if not existing_form:
                raise HTTPException(status_code=404, detail=f"Form with ID {form_id} does not exist")

            # Check ownership
            if existing_form.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"User {current_user.id} does not have permission to modify form {form_id}"
                )

            # Update form fields
            updated_fields = []
            if api_cmd.new_webhook_url is not None:
                existing_form.webhook_url = str(api_cmd.new_webhook_url)
                updated_fields.append("webhook_url")

            # Status updates are not part of the API command in this endpoint
            existing_form.updated_at = datetime.now(UTC)
            updated_fields.append("updated_at")

            await uow.commit()

            # Create success response (same as Lambda implementation)
            response = FormManagementResponse(
                success=True,
                operation=FormOperationType.UPDATE,
                form_id=form_id,
                message=f"Form {form_id} updated successfully",
                created_form_id=None,
                updated_fields=updated_fields,
                webhook_status="updated",
                operation_timestamp=datetime.now(UTC),
                execution_time_ms=None,
                error_code=None,
                error_details=None,
                warnings=[],
            )

        return create_success_response(response.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update form: {str(e)}")


@router.delete("/forms/{form_id}")
async def delete_form(
    form_id: int,
    bus: MessageBus = Depends(get_clients_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete onboarding form."""
    try:
        # Execute business logic using MessageBus (same as Lambda implementation)
        api_cmd = ApiDeleteOnboardingForm(form_id=form_id)
        cmd = api_cmd.to_domain(user_id=current_user.id)
        await bus.handle(cmd)

        return create_success_response(
            {
                "message": "Form deleted successfully",
                "details": {"form_id": form_id, "user_id": str(current_user.id)},
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete form: {str(e)}")


# Webhook endpoints

@router.post("/webhook")
async def process_webhook(
    request: Request,
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Process TypeForm webhook payload."""
    try:
        # Extract webhook payload and headers (same as Lambda implementation)
        body = await request.body()
        raw_body = body.decode('utf-8') if isinstance(body, bytes) else str(body)
        
        headers = dict(request.headers)

        # Process webhook by dispatching a command through the MessageBus
        api_cmd = ApiProcessWebhook(payload=raw_body, headers=headers)
        cmd = api_cmd.to_domain()
        await bus.handle(cmd)

        return create_success_response(
            {
                "message": "Webhook processed successfully",
                "details": {"processed_at": datetime.now(UTC).isoformat() + "Z"},
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process webhook: {str(e)}")


# Query responses endpoints

@router.post("/query-responses")
async def query_responses(
    request_body: ResponseQueryRequest,
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Execute single response query."""
    try:
        # Execute query (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            ownership_validator = FormOwnershipValidator()
            result = await execute_query(request_body, uow, ownership_validator)
            await uow.commit()

        return create_success_response(result.model_dump())
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to execute query: {str(e)}")


@router.post("/bulk-query-responses")
async def bulk_query_responses(
    request_body: BulkResponseQueryRequest,
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Execute multiple response queries."""
    try:
        # Execute queries (same as Lambda implementation)
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
                    from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import ResponseQueryResponse
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

        # Create bulk response (same as Lambda implementation)
        from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import BulkResponseQueryResponse
        bulk_response = BulkResponseQueryResponse(
            success=successful_queries == len(request_body.queries),
            total_queries=len(request_body.queries),
            successful_queries=successful_queries,
            results=results,
            errors=errors if errors else None,
        )

        return create_success_response(bulk_response.model_dump())
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to execute bulk queries: {str(e)}")
