import logging

from src.logging.logger import logger

from ..domain.commands import (
    AddHouseInvitation,
    AddPatient,
    CreateNutritionist,
    DeletePatient,
    EditBrandNote,
    EditPatientBrandNote,
    EditPatientProductNote,
    EditProductNote,
    LeaveHouse,
    LinkPatient,
    RespondHouseInvitation,
    UnlinkPatient,
    UpdatePatientProperty,
    UpdateProperty,
)
from ..domain.entities import Nutritionist
from .unit_of_work import UnitOfWork


def create_nutritionist(cmd: CreateNutritionist, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = Nutritionist.create_nutritionist(
            user_id=cmd.user_id,
            user_name=cmd.user_name,
            email=cmd.email,
        )
        uow.nutritionists.add(nutritionist)
        uow.commit()


def update_property(cmd: UpdateProperty, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.user_id)
        nutritionist.update_properties(**cmd.property_value)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def add_patient(cmd: AddPatient, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.add_patient(cmd.contact)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def update_patient_property(cmd: UpdatePatientProperty, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.update_patient_properties(
            patient_id=cmd.patient_id, **cmd.property_value
        )
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def delete_patient(cmd: DeletePatient, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.delete_patient(cmd.patient_id)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def link_patient(cmd: LinkPatient, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.link_patient(cmd.patient_id, cmd.user_id)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def unlink_patient(cmd: UnlinkPatient, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.unlink_patient(cmd.patient_id)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def add_house_invitation(cmd: AddHouseInvitation, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.add_house_invitation(cmd.house_id)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def responde_house_invitation(cmd: RespondHouseInvitation, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        if cmd.response:
            nutritionist.accept_house_invitation(cmd.house_id)
        elif cmd.response is False:
            nutritionist.decline_house_invitation(cmd.house_id)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def leave_house(cmd: LeaveHouse, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.user_id)
        nutritionist.leave_house(cmd.house_id)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def edit_product_note(cmd: EditProductNote, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.edit_product_notes(cmd.produt_id, cmd.notes)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def edit_brand_note(cmd: EditBrandNote, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.edit_brand_notes(cmd.brand, cmd.notes)
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def edit_patient_product_note(cmd: EditPatientProductNote, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.edit_patient_product_notes(
            cmd.patient_id, cmd.produt_id, cmd.notes
        )
        uow.nutritionists.persist(nutritionist)
        uow.commit()


def edit_patient_brand_note(cmd: EditPatientBrandNote, uow: UnitOfWork) -> None:
    with uow:
        nutritionist = uow.nutritionists.get(cmd.nutritionist_id)
        nutritionist.edit_patient_brand_notes(cmd.patient_id, cmd.brand, cmd.notes)
        uow.nutritionists.persist(nutritionist)
        uow.commit()
