from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command

from ...common.value_objects import Contact
from .value_objects import ProductNotes


@frozen
class CreateNutritionist(Command):
    user_id: str
    user_name: str
    email: str


@frozen
class UpdateProperty(Command):
    user_id: str
    property_value = dict[str, Any]


@frozen
class AddPatient(Command):
    nutritionist_id: str
    contact: Contact


@frozen
class DeletePatient(Command):
    nutritionist_id: str
    patient_id: str


@frozen
class UpdatePatientProperty(Command):
    nutritionist_id: str
    patient_id: str
    property_value = dict[str, Any]


@frozen
class LinkPatient(Command):
    nutritionist_id: str
    patient_id: str
    user_id: str


@frozen
class UnlinkPatient(Command):
    nutritionist_id: str
    patient_id: str


@frozen
class AddHouseInvitation(Command):
    nutritionist_id: str
    house_id: str


@frozen
class RespondHouseInvitation(Command):
    nutritionist_id: str
    house_id: str
    response: bool


@frozen
class LeaveHouse(Command):
    user_id: str
    house_id: str


@frozen
class EditProductNote(Command):
    nutritionist_id: str
    produt_id: str
    notes: ProductNotes


@frozen
class EditBrandNote(Command):
    nutritionist_id: str
    brand: str
    notes: ProductNotes


@frozen
class EditPatientProductNote(Command):
    nutritionist_id: str
    patient_id: str
    produt_id: str
    notes: ProductNotes


@frozen
class EditPatientBrandNote(Command):
    nutritionist_id: str
    patient_id: str
    brand: str
    notes: ProductNotes
