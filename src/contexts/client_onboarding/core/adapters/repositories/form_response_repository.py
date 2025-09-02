"""
Repository: Form Response

SQLAlchemy repository for managing form response database operations.
Provides async CRUD operations for TypeForm response data storage.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse


class FormResponseRepo:
    """SQLAlchemy repository for FormResponse database operations.

    Provides async CRUD operations for storing and retrieving TypeForm response data.
    Works directly with SQLAlchemy models for simplicity in this context.

    Notes:
        Adheres to repository pattern. Methods require active UnitOfWork session.
        Uses SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.

        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session

    async def add(self, form_response: FormResponse) -> FormResponse:
        """Add a new form response to the database.

        Args:
            form_response: FormResponse object to persist

        Returns:
            FormResponse: Added form response with generated ID
        """
        self.session.add(form_response)
        await self.session.flush()  # Get ID without committing
        return form_response

    async def get_all(self) -> list[FormResponse]:
        """Retrieve all form responses from the database.

        Returns:
            List of all FormResponse objects
        """
        stmt = select(FormResponse)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, response_id: int) -> FormResponse | None:
        """Get form response by internal database ID.

        Args:
            response_id: Internal form response ID

        Returns:
            FormResponse object if found, None otherwise
        """
        stmt = select(FormResponse).where(FormResponse.id == response_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_response_id(self, response_id: str) -> FormResponse | None:
        """Get form response by TypeForm response ID.

        Args:
            response_id: TypeForm response ID

        Returns:
            FormResponse object if found, None otherwise
        """
        stmt = select(FormResponse).where(FormResponse.response_id == response_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_form_id(self, form_id: int) -> list[FormResponse]:
        """Get all responses for a specific onboarding form.

        Args:
            form_id: Internal onboarding form ID

        Returns:
            List of FormResponse objects for the specified form
        """
        stmt = select(FormResponse).where(FormResponse.form_id == form_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, form_response: FormResponse) -> FormResponse:
        """Update an existing form response.

        Args:
            form_response: FormResponse object with updated data

        Returns:
            Updated FormResponse object
        """
        # SQLAlchemy automatically tracks changes to attached objects
        await self.session.flush()
        return form_response
