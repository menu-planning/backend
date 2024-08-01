import logging

from src.celery.app_worker import celery_app
from src.logging.logger import logger

from ..domain.events import (
    NutritionistAcceptedHouseInvitation,
    NutritionistCreated,
    NutritionistDeclinedHouseInvitation,
    NutritionistLeftHouse,
    PatientLinkedUser,
    PatientUnlinkedUser,
)
from .unit_of_work import UnitOfWork


def send_new_nutritionits_notification(event: NutritionistCreated) -> None:
    celery_app.send_task(
        "core.tasks.send_new_nutritionist_notification",
        kwargs={"id": event.user_id},
    )


def publish_house_invitation_accepted(
    event: NutritionistAcceptedHouseInvitation,
) -> None:
    celery_app.send_task(
        "collaboration.tasks.house_invitation_accepeted",
        kwargs={
            "user_id": event.user_id,
            "house_id": event.house_id,
        },
    )


def publish_house_invitation_declined(
    event: NutritionistDeclinedHouseInvitation,
) -> None:
    celery_app.send_task(
        "collaboration.tasks.house_invitation_declined",
        kwargs={
            "user_id": event.user_id,
            "house_id": event.house_id,
        },
    )


def publish_link_patient(event: PatientLinkedUser) -> None:
    celery_app.send_task(
        "collaboration.tasks.link_patient",
        kwargs={
            "nutritionist_id": event.nutritionist_id,
            "patient_id": event.patient_id,
            "user_id": event.user_id,
        },
    )


def publish_unlink_patient(event: PatientUnlinkedUser) -> None:
    celery_app.send_task(
        "collaboration.tasks.unlink_patient",
        kwargs={
            "nutritionist_id": event.nutritionist_id,
            "patient_id": event.patient_id,
            "user_id": event.user_id,
        },
    )


def publish_nutritionist_left_house(event: NutritionistLeftHouse) -> None:
    celery_app.send_task(
        "collaboration.tasks.remove_nutritionist_from_house",
        kwargs={
            "user_id": event.user_id,
            "house_id": event.house_id,
        },
    )
