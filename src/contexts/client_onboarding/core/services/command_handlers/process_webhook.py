"""
Process Webhook Command Handler

Validates and persists a Typeform webhook by leveraging the existing
WebhookPayloadProcessor pipeline. Errors are raised as exceptions so
the MessageBus can propagate them to the caller.
"""

from __future__ import annotations

import logging
import json

from src.contexts.client_onboarding.core.domain.commands.process_webhook import (
    ProcessWebhookCommand,
)
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookPayloadProcessor,
    WebhookSecurityVerifier,
)

from ..uow import UnitOfWork


logger = logging.getLogger(__name__)


async def process_webhook_handler(
    cmd: ProcessWebhookCommand,
    uow: UnitOfWork,
) -> None:
    """
    Handle Typeform webhook processing.

    On success, completes without returning a value. On failure, raises a
    domain-specific exception to be handled by the caller.
    """
    logger.info("Processing webhook via command handler")

    # Parse payload JSON or raise
    try:
        payload_dict = json.loads(cmd.payload)
    except json.JSONDecodeError as e:
        # Normalize to same error class as processor uses
        from src.contexts.client_onboarding.core.services.exceptions import WebhookPayloadError

        raise WebhookPayloadError(f"Invalid JSON payload: {str(e)}") from e

    async with uow:
        processor = WebhookPayloadProcessor(uow)
        processed = await processor.process_webhook_payload(payload_dict)
        _response_id = await processor.store_form_response(processed)

    # Best-effort mark processed (non-fatal if it fails)
    try:
        await WebhookSecurityVerifier.mark_request_processed(cmd.payload, cmd.headers)
    except Exception:
        pass


