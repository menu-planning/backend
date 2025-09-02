from __future__ import annotations

from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class ProcessWebhookCommand(Command):
    """Command to process an incoming Typeform webhook payload.

    Args:
        payload: Raw webhook payload string from Typeform.
        headers: HTTP headers from the webhook request.
        result: Optional mutable container to receive processing results from the handler.

    Notes:
        The handler validates the payload, verifies the form, extracts client
        identifiers, and persists a normalized response record.
    """

    payload: str
    headers: dict[str, str]
    result: dict[str, Any] | None = None
