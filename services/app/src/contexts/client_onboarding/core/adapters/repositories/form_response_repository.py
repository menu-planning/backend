"""
FormResponse Repository

Async repository for managing form response database operations.
Uses SQLAlchemy models directly for simplicity in this context.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.client_onboarding.models.form_response import FormResponse


class FormResponseRepo:
    """
    Async repository for FormResponse operations.
    
    Simplified repository that works directly with SQLAlchemy models
    for storing and retrieving TypeForm response data.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, form_response: FormResponse) -> FormResponse:
        """Add a new form response."""
        self.session.add(form_response)
        await self.session.flush()  # Get ID without committing
        return form_response
    
    async def get_by_id(self, response_id: int) -> Optional[FormResponse]:
        """Get form response by ID."""
        stmt = select(FormResponse).where(FormResponse.id == response_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_response_id(self, response_id: str) -> Optional[FormResponse]:
        """Get form response by TypeForm response ID."""
        stmt = select(FormResponse).where(FormResponse.response_id == response_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_form_id(self, form_id: int) -> List[FormResponse]:
        """Get all responses for a specific onboarding form."""
        stmt = select(FormResponse).where(FormResponse.form_id == form_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, form_response: FormResponse) -> FormResponse:
        """Update an existing form response."""
        # SQLAlchemy automatically tracks changes to attached objects
        await self.session.flush()
        return form_response 