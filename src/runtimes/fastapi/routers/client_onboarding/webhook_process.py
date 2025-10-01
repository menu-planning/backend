"""FastAPI router for webhook processing endpoint."""

from fastapi import Depends, Request
from typing import Any

from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_process_webhook import (
    ApiProcessWebhook,
)
from src.contexts.client_onboarding.fastapi.dependencies import get_clients_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)
from datetime import datetime, UTC

router = create_router(prefix="/client-onboarding")


@router.post("/webhook")
async def process_webhook(
    request: Request,
    bus: MessageBus = Depends(get_clients_bus),
) -> Any:
    """Process TypeForm webhook payload.
    
    Args:
        request: FastAPI Request object containing webhook payload
        bus: Message bus for business logic
        
    Returns:
        Success response with processing details
    """
    # Extract webhook payload and headers
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
