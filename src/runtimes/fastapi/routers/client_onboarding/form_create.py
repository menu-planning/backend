"""FastAPI router for form creation endpoint."""

from fastapi import Depends
from typing import Annotated, Any

from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_setup_onboarding_form import (
    ApiSetupOnboardingForm,
)
from src.contexts.client_onboarding.fastapi.dependencies import get_clients_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_client_onboarding_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/client-onboarding", tags=["client-onboarding"])


@router.post("/forms")
async def create_form(
    request_body: ApiSetupOnboardingForm,
    current_user: Annotated[Any, Depends(get_client_onboarding_user)],
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Create new onboarding form.
    
    Args:
        request_body: Form setup data
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        Success response with form details
    """
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
