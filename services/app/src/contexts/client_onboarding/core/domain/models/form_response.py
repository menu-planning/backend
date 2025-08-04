from __future__ import annotations

from datetime import datetime
from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, TYPE_CHECKING

from src.db.base import SaBase, SerializerMixin

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm


class FormResponse(SerializerMixin, SaBase):
    """
    SQLAlchemy ORM model for storing TypeForm response data
    
    Stores individual form submissions with flexible JSON data storage
    and client identification information
    """
    __tablename__ = "form_responses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("client_onboarding.onboarding_forms.id"), index=True)
    
    # TypeForm response data stored as JSONB for flexibility
    response_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Client identification fields for data correlation
    client_identifiers: Mapped[Dict[str, Any] | None] = mapped_column(JSON)  # Store email, phone, user_id, etc.
    
    # TypeForm specific fields
    response_id: Mapped[str] = mapped_column(Text, unique=True, index=True)  # TypeForm response ID
    submission_id: Mapped[str | None] = mapped_column(Text, index=True)  # TypeForm submission ID
    
    # Audit fields
    submitted_at: Mapped[datetime]  # From TypeForm
    processed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    # Relationship to OnboardingForm
    onboarding_form: Mapped["OnboardingForm"] = relationship("OnboardingForm", back_populates="responses")

    __table_args__ = (
        {"schema": "client_onboarding", "extend_existing": True},
    )
    
    def __repr__(self) -> str:
        return f"<FormResponse(id={self.id}, form_id={self.form_id}, response_id='{self.response_id}')>" 