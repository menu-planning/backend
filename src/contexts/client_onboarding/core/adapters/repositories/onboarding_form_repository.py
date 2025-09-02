"""
Repository: Onboarding Form

SQLAlchemy repository for managing onboarding form database operations.
Provides async CRUD operations for TypeForm integration and form management.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
    OnboardingFormStatus,
)


class OnboardingFormRepo:
    """SQLAlchemy repository for OnboardingForm database operations.

    Provides async CRUD operations for managing TypeForm integration and
    onboarding form configurations. Works directly with SQLAlchemy models
    for simplicity in this context.

    Notes:
        Adheres to repository pattern. Methods require active UnitOfWork session.
        Implements soft deletion by updating status rather than removing records.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.

        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session

    async def add(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Add a new onboarding form to the database.

        Args:
            onboarding_form: OnboardingForm object to persist

        Returns:
            OnboardingForm: Added form with generated ID
        """
        self.session.add(onboarding_form)
        await self.session.flush()  # Get ID without committing
        return onboarding_form

    async def get_all(self) -> list[OnboardingForm]:
        """Retrieve all onboarding forms from the database.

        Returns:
            List of all OnboardingForm objects
        """
        stmt = select(OnboardingForm)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, form_id: int) -> OnboardingForm | None:
        """Get onboarding form by internal database ID.

        Args:
            form_id: Internal onboarding form ID

        Returns:
            OnboardingForm object if found, None otherwise
        """
        stmt = select(OnboardingForm).where(OnboardingForm.id == form_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_typeform_id(self, typeform_id: str) -> OnboardingForm | None:
        """Get onboarding form by TypeForm ID.

        Excludes soft-deleted forms from results.

        Args:
            typeform_id: TypeForm form ID

        Returns:
            OnboardingForm object if found, None otherwise
        """
        stmt = select(OnboardingForm).where(
            OnboardingForm.typeform_id == typeform_id,
            OnboardingForm.status != OnboardingFormStatus.DELETED,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[OnboardingForm]:
        """Get all onboarding forms for a specific user.

        Excludes soft-deleted forms from results.

        Args:
            user_id: User ID to filter forms by

        Returns:
            List of OnboardingForm objects owned by the user
        """
        stmt = select(OnboardingForm).where(
            OnboardingForm.user_id == user_id,
            OnboardingForm.status != OnboardingFormStatus.DELETED,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Update an existing onboarding form.

        Args:
            onboarding_form: OnboardingForm object with updated data

        Returns:
            Updated OnboardingForm object
        """
        # SQLAlchemy automatically tracks changes to attached objects
        await self.session.flush()
        return onboarding_form

    async def delete(self, onboarding_form: OnboardingForm) -> None:
        """Soft delete an onboarding form.

        Updates form status to DELETED rather than removing the record.

        Args:
            onboarding_form: OnboardingForm object to soft delete
        """
        onboarding_form.status = OnboardingFormStatus.DELETED
        await self.session.flush()
