from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from src.db.base import SaBase, SerializerMixin

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse


class OnboardingFormStatus(PyEnum):
    """Status enum for onboarding forms"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DELETED = "deleted"


class OnboardingForm(SerializerMixin, SaBase):
    """
    SQLAlchemy ORM model for onboarding form configuration
    
    Stores TypeForm integration settings for user onboarding workflows
    """
    __tablename__ = "onboarding_forms"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(index=True)
    typeform_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    webhook_url: Mapped[str] = mapped_column(Text)
    status: Mapped[OnboardingFormStatus] = mapped_column(
        ENUM(
            OnboardingFormStatus,
            name="onboardingformstatus",
            schema="client_onboarding",
            create_type=False,
            values_callable=lambda x: [item.value for item in x]
        ),
        default=OnboardingFormStatus.DRAFT
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    # Relationship to FormResponse
    responses: Mapped[list["FormResponse"]] = relationship("FormResponse", back_populates="onboarding_form")

    __table_args__ = (
        {"schema": "client_onboarding", "extend_existing": True},
    )
    
    def __repr__(self) -> str:
        return f"<OnboardingForm(id={self.id}, user_id={self.user_id}, typeform_id='{self.typeform_id}', status='{self.status.value}')>" 