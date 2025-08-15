"""
OnboardingForm Repository

Async repository for managing onboarding form database operations.
Uses SQLAlchemy models directly for simplicity in this context.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus


class OnboardingFormRepo:
    """
    Async repository for OnboardingForm operations.
    
    Simplified repository that works directly with SQLAlchemy models
    since this context focuses on data storage rather than complex business logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Add a new onboarding form."""
        self.session.add(onboarding_form)
        await self.session.flush()  # Get ID without committing
        return onboarding_form
    
    async def get_all(self) -> List[OnboardingForm]:
        """Get all onboarding forms."""
        stmt = select(OnboardingForm)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id(self, form_id: int) -> Optional[OnboardingForm]:
        """Get onboarding form by ID."""
        stmt = select(OnboardingForm).where(OnboardingForm.id == form_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_typeform_id(self, typeform_id: str) -> Optional[OnboardingForm]:
        """Get onboarding form by TypeForm ID."""
        stmt = select(OnboardingForm).where(
            OnboardingForm.typeform_id == typeform_id,
            OnboardingForm.status != OnboardingFormStatus.DELETED
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str) -> List[OnboardingForm]:
        """Get all onboarding forms for a specific user."""
        stmt = select(OnboardingForm).where(
            OnboardingForm.user_id == user_id,
            OnboardingForm.status != OnboardingFormStatus.DELETED
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Update an existing onboarding form."""
        # SQLAlchemy automatically tracks changes to attached objects
        await self.session.flush()
        return onboarding_form
    
    async def delete(self, onboarding_form: OnboardingForm) -> None:
        """Soft delete an onboarding form."""
        onboarding_form.status = OnboardingFormStatus.DELETED
        await self.session.flush() 