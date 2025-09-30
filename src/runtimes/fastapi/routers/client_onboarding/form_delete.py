"""FastAPI router for form deletion endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_delete_onboarding_form import (
    ApiDeleteOnboardingForm,
)
from src.contexts.client_onboarding.fastapi.dependencies import get_clients_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_client_onboarding_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/client-onboarding", tags=["client-onboarding"])


@router.delete("/forms/{form_id}")
async def delete_form(
    form_id: int,
    current_user: Annotated[Any, Depends(get_client_onboarding_user)],
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Delete onboarding form.
    
    Args:
        form_id: ID of the form to delete
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success response with deletion details
    """
    api_cmd = ApiDeleteOnboardingForm(form_id=form_id)
    cmd = api_cmd.to_domain(user_id=current_user.id)
    await bus.handle(cmd)

    return create_success_response(
        {
            "message": "Form deleted successfully",
            "details": {"form_id": form_id, "user_id": str(current_user.id)},
        }
    )
