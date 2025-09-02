"""Domain command to delete a client aggregate."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteClient(Command):
    """Command to delete an existing client.

    Args:
        client_id: ID of the client to delete
    """
    client_id: str
