from attrs import frozen

from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.tag import Tag

@frozen(kw_only=True)
class CreateClient(Command):
    """Command to create a new client."""

    author_id: str
    profile: Profile
    contact_info: ContactInfo | None = None
    address: Address| None = None
    notes: str | None = None
    tags: set[Tag] | None = None