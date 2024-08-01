import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class HouseholdCreated(Event):
    owner_id: str
    name: str
    house_id: str = field(factory=lambda: uuid.uuid4().hex)
