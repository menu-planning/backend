import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Privacy


@frozen
class TagCreated(Event):
    name: str
    author_id: str
    privacy: Privacy
    description: str | None = None
    tag_id: str = field(factory=lambda: uuid.uuid4().hex)
