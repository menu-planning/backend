"""
Fake Unit of Work implementation for Client Onboarding testing.

This fake UoW provides in-memory repositories for isolated testing without database dependencies.
Follows the same patterns as the products catalog fake implementations.
"""

from __future__ import annotations
from unittest.mock import Mock

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.contexts.client_onboarding.core.services.uow import UnitOfWork

from .fake_onboarding_repositories import (
    FakeOnboardingFormRepository,
    FakeFormResponseRepository,
)


class FakeUnitOfWork(UnitOfWork):
    """
    Fake Unit of Work implementation for client onboarding testing.
    
    Provides the same interface as the real UnitOfWork but uses in-memory
    fake repositories instead of database-backed ones.
    """
    
    def __init__(self):
        # Create a mock session factory to satisfy parent class requirements
        mock_session_factory: async_sessionmaker[AsyncSession] = Mock()
        super().__init__(mock_session_factory)
        
        self.committed = False
        self.rolled_back = False
        
        # Initialize all fake repositories
        self.onboarding_forms = FakeOnboardingFormRepository()
        self.form_responses = FakeFormResponseRepository()
        
        # Mock session for compatibility
        self.session = Mock()

    async def __aenter__(self):
        """Support async context manager protocol."""
        # Override the abstract method - no need to create real session
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Gracefully handle context manager exit."""
        if exc_type is not None:
            await self.rollback()
        await self.close()

    async def commit(self):
        """Mark the unit of work as committed."""
        self.committed = True

    async def rollback(self):
        """Mark the unit of work as rolled back."""
        self.rolled_back = True

    async def close(self):
        """Close the unit of work - no-op for fake implementation."""
        pass

    def collect_new_events(self):
        """
        Collect domain events from all tracked entities.
        
        Yields events from all repositories' seen entities.
        """
        # Check all repositories for entities with events
        repositories = [
            self.onboarding_forms,
            self.form_responses,
        ]
        
        for repo in repositories:
            for entity in repo.seen:
                if hasattr(entity, 'events'):
                    while entity.events:
                        yield entity.events.pop(0) 