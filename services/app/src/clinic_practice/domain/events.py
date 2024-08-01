import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class NutritionistCreated(Event):
    user_id: str
    nutritionist_id: str = field(default=uuid.uuid4().hex)


@frozen
class NutritionistAcceptedHouseInvitation(Event):
    nutritionist_id: str
    house_id: str


@frozen
class NutritionistDeclinedHouseInvitation(Event):
    user_id: str
    house_id: str


@frozen
class PatientLinkedUser(Event):
    # nutritionist_id: str
    patient_id: str
    user_id: str


@frozen
class PatientUnlinkedUser(Event):
    # nutritionist_id: str
    patient_id: str
    user_id: str


@frozen
class NutritionistLeftHouse(Event):
    user_id: str
    house_id: str
