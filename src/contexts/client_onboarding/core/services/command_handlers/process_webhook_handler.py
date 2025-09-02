"""Process webhook command handler for TypeForm webhooks.

Validates and persists TypeForm webhook payloads by leveraging the existing
WebhookPayloadProcessor pipeline. Errors are raised as exceptions so the
MessageBus can propagate them to the caller.
"""

from __future__ import annotations

import json

from src.contexts.client_onboarding.core.domain.commands.process_webhook import (
    ProcessWebhookCommand,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookPayloadProcessor,
)
from src.contexts.client_onboarding.core.services.webhooks.security import WebhookSecurityVerifier
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


async def process_webhook_handler(
    cmd: ProcessWebhookCommand,
    uow: UnitOfWork,
) -> None:
    """Handle TypeForm webhook processing.

    Processes incoming TypeForm webhook payloads by parsing JSON, validating
    the payload structure, and storing the form response data. On success,
    completes without returning a value. On failure, raises a domain-specific
    exception to be handled by the caller.

    Args:
        cmd: Process webhook command containing payload and headers.
        uow: Unit of work for database operations.

    Raises:
        WebhookPayloadError: For invalid JSON payload or processing errors.
        FormResponseProcessingError: For form response processing failures.
        OnboardingFormNotFoundError: If the form is not found in the database.
    """
    logger.info(
        "Processing webhook",
        action="process_webhook",
        payload_size=len(cmd.payload),
        headers_count=len(cmd.headers),
        webhook_source="typeform",
        processing_stage="initialization"
    )

    # Parse payload JSON or raise
    try:
        payload_dict = json.loads(cmd.payload)
        event_id = payload_dict.get('event_id')
        form_id = payload_dict.get('form_response', {}).get('form_id')

        logger.debug(
            "Webhook payload parsed successfully",
            action="process_webhook_parsed",
            event_id=event_id,
            form_id=form_id,
            webhook_source="typeform",
            processing_stage="json_parsing_success"
        )
    except json.JSONDecodeError as e:
        # Normalize to same error class as processor uses
        from src.contexts.client_onboarding.core.services.exceptions import (
            WebhookPayloadError,
        )

        logger.error(
            "Invalid JSON payload in webhook",
            action="process_webhook_error",
            error_type="JSONDecodeError",
            error_message=str(e),
            payload_preview=cmd.payload[:100] if len(cmd.payload) > 100 else cmd.payload,
            webhook_source="typeform",
            processing_stage="json_parsing",
            payload_size=len(cmd.payload),
            headers_count=len(cmd.headers),
            business_impact="webhook_rejected"
        )
        raise WebhookPayloadError(f"Invalid JSON payload: {e!s}") from e

    try:
        async with uow:
            processor = WebhookPayloadProcessor(uow)
            processed = await processor.process_webhook_payload(payload_dict)
            response_id = await processor.store_form_response(processed)

        logger.info(
            "Webhook processed successfully",
            action="process_webhook_success",
            response_id=response_id,
            form_id=processed.form_id if processed else None,
            event_id=processed.event_id if processed else None,
            event_type=processed.event_type if processed else None,
            webhook_source="typeform",
            processing_stage="completed",
            business_impact="form_response_stored",
            client_identifiers_count=len(processed.client_identifiers) if processed and processed.client_identifiers else 0,
            field_responses_count=len(processed.field_responses) if processed and processed.field_responses else 0
        )

        # Best-effort mark processed (non-fatal if it fails)
        try:
            await WebhookSecurityVerifier.mark_request_processed(cmd.payload, cmd.headers)
            logger.debug(
                "Webhook marked as processed",
                action="webhook_security_mark_processed",
                response_id=response_id,
                form_id=processed.form_id if processed else None,
                webhook_source="typeform",
                security_stage="replay_protection_applied"
            )
        except Exception as e:
            logger.warning(
                "Failed to mark webhook as processed",
                action="webhook_security_mark_failed",
                response_id=response_id,
                error_type=type(e).__name__,
                error_message=str(e),
                form_id=processed.form_id if processed else None,
                webhook_source="typeform",
                security_stage="replay_protection_failed",
                business_impact="security_warning_only"
            )
    except Exception as e:
        logger.error(
            "Failed to process webhook",
            action="process_webhook_error",
            error_type=type(e).__name__,
            error_message=str(e),
            event_id=event_id,
            form_id=form_id,
            webhook_source="typeform",
            processing_stage="failed",
            business_impact="webhook_processing_failed",
            payload_size=len(cmd.payload),
            exc_info=True
        )
        raise


