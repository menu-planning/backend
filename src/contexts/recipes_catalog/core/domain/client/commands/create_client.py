"""Domain command to create a client aggregate."""
from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateClient(Command):
    """Command to create a new client.

    Args:
        author_id: ID of the user creating the client
        profile: Client profile information
        contact_info: Client contact information (optional)
        address: Client address information (optional)
        notes: Additional notes about the client (optional)
        tags: Set of tags to associate with the client (optional)
        form_response_id: ID of the form response (optional)
    """

    author_id: str
    profile: Profile
    contact_info: ContactInfo | None = None
    address: Address| None = None
    notes: str | None = None
    tags: frozenset[Tag] | None = None
    form_response_id: str | None = None
