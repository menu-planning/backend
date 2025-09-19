"""
Webhook Testing Utilities

Testing utilities for webhook processing that bypass the normal MessageBus
architecture for easier testing and debugging.
"""

import json
from typing import Any

from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookPayloadProcessor,
    WebhookSecurityVerifier,
)
from src.logging.logger import get_logger

logger = get_logger(__name__)


class WebhookProcessor:
    """Testing utility for webhook processing that bypasses MessageBus."""
    
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    async def process_webhook(self, payload: str, headers: dict[str, str]) -> tuple[bool, str | None, str | None]:
        """Process webhook for testing purposes, bypassing MessageBus."""
        async with self.uow_factory() as uow:
            try:
                processor = WebhookPayloadProcessor(uow)
                try:
                    payload_dict = json.loads(payload)
                except json.JSONDecodeError as e:
                    return False, f"Invalid JSON payload: {e!s}", None
                processed_data = await processor.process_webhook_payload(payload_dict)
                response_id = await processor.store_form_response(processed_data)
                try:
                    await WebhookSecurityVerifier.mark_request_processed(payload, headers)
                except Exception:
                    pass
                return True, None, response_id
            except Exception as e:
                logger.error("Webhook processing failed", error=str(e), action="webhook_processing_failure", exc_info=True)
                return False, str(e), None


async def process_typeform_webhook(payload: str, headers: dict[str, str], uow_factory) -> tuple[bool, str | None, str | None]:
    """Testing entry point for webhook processing that bypasses MessageBus."""
    processor = WebhookProcessor(uow_factory)
    return await processor.process_webhook(payload, headers)
