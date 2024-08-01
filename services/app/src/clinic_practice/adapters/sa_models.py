from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.nutrition_assessment_and_planning.modules.common.sa_models import (
    BrandNotesSaModel,
    ContactableSaModel,
    ProductNotesSaModel,
)

from ..domain.value_objects import CRN


class PatientSaModel(ContactableSaModel):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        ForeignKey("core.contactables.id"), primary_key=True
    )
    nutritionist_id: Mapped[str] = mapped_column(ForeignKey("core.nutritionists.id"))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("core.users.id"))
    house: Mapped[str | None]
    pending_user_link: Mapped[str | None]
    products_notes: Mapped[list[ProductNotesSaModel]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    brands_notes: Mapped[list[BrandNotesSaModel]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        "polymorphic_identity": "patient",
    }

    __table_args__ = {"schema": "core"}


class NutritionistSaModel(ContactableSaModel):
    __tablename__ = "nutritionists"

    id: Mapped[str] = mapped_column(
        ForeignKey("core.contactables.id"), primary_key=True
    )
    login_email: Mapped[str] = mapped_column(index=True, unique=True)
    crn_number: Mapped[str | None] = mapped_column(index=True)
    crn_state: Mapped[str | None]
    patients: Mapped[list[PatientSaModel]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    houses: Mapped[set[str]]
    pending_house_invitations: Mapped[set[str]]
    products_notes: Mapped[list[ProductNotesSaModel]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    brands_notes: Mapped[list[BrandNotesSaModel]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    crn: Mapped[CRN] = composite("crn_number", "crn_state")

    __mapper_args__ = {
        "polymorphic_identity": "nutritionist",
    }

    __table_args__ = {"schema": "core"}
