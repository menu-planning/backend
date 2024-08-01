# import logging

# from fastapi import APIRouter, Depends,Query,
# from src.api import deps

# from ..adapters.api_schemas import ApiNutritionistBase
# from ..domain.commands import (
#     AddHouseInvitation,
#     CreateNutritionist,
#     LinkPatient,
#     UnlinkPatient,
# )

# from src.logging.logger import logger
# router = APIRouter()


# @celery_app.task(
#     name="clinic.tasks.create_nutritionist",
#     ignore_result=True,
#     bind=True,
# )
# def create_nutritionist(self, email: str) -> None:
#     bus = container.Container().bootstrap()
#     command = CreateNutritionist(email=email)
#     bus.handle(command)


# @celery_app.task(
#     name="clinic.tasks.link_patient",
#     ignore_result=True,
#     bind=True,
# )
# def link_patient(
#     self, nutritionist_id: str, patient_id: str, user_id: str
# ) -> None:
#     bus = container.Container().bootstrap()
#     command = LinkPatient(
#         nutritionist_id=nutritionist_id, patient_id=patient_id, user_id=user_id
#     )
#     bus.handle(command)


# @celery_app.task(
#     name="clinic.tasks.unlink_patient",
#     ignore_result=True,
#     bind=True,
# )
# def unlink_patient(self, nutritionist_id: str, patient_id: str) -> None:
#     bus = container.Container().bootstrap()
#     command = UnlinkPatient(
#         nutritionist_id=nutritionist_id, patient_id=patient_id
#     )
#     bus.handle(command)


# @celery_app.task(
#     name="clinic.tasks.add_house_invitation",
#     ignore_result=True,
#     bind=True,
# )
# def add_house_invitation(self, nutritionist_id: str, house_id: str) -> None:
#     bus = container.Container().bootstrap()
#     command = AddHouseInvitation(
#         nutritionist_id=nutritionist_id, house_id=house_id
#     )
#     bus.handle(command)


# @router.get("/", response_model=list[ApiNutritionistBase])
# def read_nutritionists(
#     email: str | None = None,
#     first_name: str | None = Query(default=None, alias="first-name"),
#     last_name: str | None = Query(default=None, alias="last-name"),
#     crn_number: str | None = Query(default=None, alias="crn-number"),
#     skip: int | None = 0,
#     limit: int | None = 500,
#     sort: str | None = "first_name",
#     current_user: entities.User = Depends(deps.get_current_active_user),
# ):
#     """
#     Retrieve users.
#     """
#     bus = container.Container().bootstrap()
#     with bus.uow as uow:
#         users = uow.users.query(skip=skip, limit=limit)
#     return users


# @router.get("/me", response_model=user_schemas.UserInDB)
# def read_user_me(
#     current_user: entities.User = Depends(deps.get_current_active_user),
# ):
#     """
#     Get current user.
#     """
#     user = current_user.encode()
#     return user
