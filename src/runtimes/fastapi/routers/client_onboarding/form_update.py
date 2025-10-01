"""FastAPI router for form update endpoint."""

from fastapi import Depends, HTTPException
from typing import Annotated, Any

from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_update_webhook_url import (
    ApiUpdateWebhookUrl,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_management import (
    FormManagementResponse,
    FormOperationType,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.fastapi.dependencies import get_clients_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_client_onboarding_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)
from datetime import datetime, UTC

router = create_router(prefix="/client-onboarding")


@router.patch("/forms/{form_id}")
async def update_form(
    form_id: int,
    request_body: ApiUpdateWebhookUrl,
    current_user: Annotated[Any, Depends(get_client_onboarding_user)],
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Update existing onboarding form.
    
    Args:
        form_id: ID of the form to update
        request_body: Update data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success response with updated form details
    """
    # Ensure path form_id overrides body form_id
    api_cmd = ApiUpdateWebhookUrl(
        form_id=form_id, 
        new_webhook_url=request_body.new_webhook_url
    )

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

        existing_form.updated_at = datetime.now(UTC)
        updated_fields.append("updated_at")

        await uow.commit()

        # Create success response
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
