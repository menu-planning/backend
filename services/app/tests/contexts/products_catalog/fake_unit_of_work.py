"""
Fake Unit of Work implementation for testing following "Architecture Patterns with Python" patterns.

This fake UoW provides in-memory repositories for isolated testing without database dependencies.
"""

from __future__ import annotations
from unittest.mock import Mock

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.contexts.seedwork.shared.services.uow import UnitOfWork

from .fake_product_repository import (
    FakeProductRepository,
    FakeBrandRepository, 
    FakeSourceRepository,
    FakeCategoryRepository,
    FakeParentCategoryRepository,
    FakeFoodGroupRepository,
    FakeProcessTypeRepository,
)


class FakeUnitOfWork(UnitOfWork):
    """
    Fake Unit of Work implementation for testing.
    
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
        self.products = FakeProductRepository()
        self.sources = FakeSourceRepository()
        self.brands = FakeBrandRepository()
        self.categories = FakeCategoryRepository()
        self.parent_categories = FakeParentCategoryRepository()
        self.food_groups = FakeFoodGroupRepository()
        self.process_types = FakeProcessTypeRepository()
        
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
            self.products,
            self.sources, 
            self.brands,
            self.categories,
            self.parent_categories,
            self.food_groups,
            self.process_types,
        ]
        
        for repo in repositories:
            for entity in repo.seen:
                if hasattr(entity, 'events'):
                    while entity.events:
                        yield entity.events.pop(0) 