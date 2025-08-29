import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class ClassificationCreated(Event):
    name: str
    author_id: str
    description: str | None = None
    classification_id: str = field(factory=lambda: uuid.uuid4().hex)
