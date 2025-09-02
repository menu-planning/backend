"""Domain command to update client fields."""
from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateClient(Command):
    """Command to update client fields.

    Args:
        client_id: ID of the client to update
        updates: Dictionary of field names and new values to update
    """
    client_id: str
    updates: dict[str, Any]
