from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from src.contexts.nutrition_assessment_and_planning.modules.common.api_schemas import (
    ApiContact,
    ApiEmail,
    ApiFullName,
)


class ApiCRNRegion(str, Enum):
    CRN_1 = "CRN-1"
    CRN_2 = "CRN-2"
    CRN_3 = "CRN-3"
    CRN_4 = "CRN-4"
    CRN_5 = "CRN-5"
    CRN_6 = "CRN-6"
    CRN_7 = "CRN-7"
    CRN_8 = "CRN-8"
    CRN_9 = "CRN-9"
    CRN_10 = "CRN-10"
    CRN_11 = "CRN-11"


class ApiCRN(BaseModel):
    region: ApiCRNRegion
    number: str


# class ApiNutritionistBase(BaseModel):
#     user_id: str
#     user_name: str
#     login_email: ApiEmail


class ApiNutritionistInDB(BaseModel):
    id: str
    user_id: str
    user_name: str
    login_email: ApiEmail


class ApiNutritionistComplete(ApiNutritionistInDB):
    id: str
    contact: ApiContact
    crn: ApiCRN | None
    patients: set[ApiPatient]
    houses: set[str]
    pending_house_invitations: set[str]
    products_notes: dict[str, ApiProductNotes]
    brands_notes: dict[str, ApiBrandNotes]
    avatat_url: str | None
    version: int = 1
    discarded: bool = False


class ApiNutritionistPublic(BaseModel):
    user_name: str
    crn: ApiCRN | None
    contact: ApiContact | None
    avatat_url: str | None


class ApiPatient(BaseModel):
    id: str | None = None
    full_name: ApiFullName | None
    houses: set[str]
    pending_patients_link: set[str]
    products_notes: dict[str, ApiProductNotes]
    brands_notes: dict[str, ApiBrandNotes]
    avatat_url: str | None
    user_id: str | None
    version: int = 1
    discarded: bool = False


class ApiProductNotes(BaseModel):
    product_id: str
    notes: str | None = None
    like: bool | None = None


class ApiBrandNotes(BaseModel):
    brand: str
    notes: str | None = None
    like: bool | None = None
