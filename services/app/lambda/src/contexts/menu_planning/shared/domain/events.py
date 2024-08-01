import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class ClientCreated(Event):
    name: str
    surname: str
    client_id: str = field(default_factory=uuid.uuid4)
