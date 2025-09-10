from __future__ import annotations

from typing import TYPE_CHECKING, Any

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import SaBase, SerializerMixin

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
        OnboardingForm,
    )


class FormResponse(SerializerMixin, SaBase):
    """SQLAlchemy ORM model for storing TypeForm response data.

    Stores individual form submissions with flexible JSON data storage
    and client identification information for correlation and processing.
    """

    __tablename__ = "form_responses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(
        ForeignKey("client_onboarding.onboarding_forms.id"), index=True
    )

    # TypeForm response data stored as JSONB for flexibility
    response_data: Mapped[dict[str, Any]] = mapped_column(JSON)

    # Client identification fields for data correlation
    client_identifiers: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # Store email, phone, user_id, etc.

    # TypeForm specific fields
    response_id: Mapped[str] = mapped_column(
        Text, unique=True, index=True
    )  # TypeForm response ID
    submission_id: Mapped[str | None] = mapped_column(
        Text, index=True
    )  # TypeForm submission ID

    # Audit fields
    submitted_at: Mapped[sa_field.datetime_tz]  # From TypeForm
    processed_at: Mapped[sa_field.datetime_tz_created]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]

    # Relationship to OnboardingForm
    onboarding_form: Mapped[OnboardingForm] = relationship(
        "OnboardingForm", back_populates="responses"
    )

    __table_args__ = ({"schema": "client_onboarding", "extend_existing": True},)

    def __repr__(self) -> str:
        return (
            f"<FormResponse(id={self.id}, form_id={self.form_id}, : "
            f"response_id='{self.response_id}')>"
        )
