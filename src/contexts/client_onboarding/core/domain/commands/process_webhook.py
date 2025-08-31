from __future__ import annotations

from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class ProcessWebhookCommand(Command):
    """
    Command to process an incoming Typeform webhook payload.

    The handler is responsible for validating the payload, verifying the form,
    extracting client identifiers, and persisting a normalized response record.
    """

    payload: str
    headers: dict[str, str]
    # Optional mutable container to receive processing results from the handler
    result: dict[str, Any] | None = None
