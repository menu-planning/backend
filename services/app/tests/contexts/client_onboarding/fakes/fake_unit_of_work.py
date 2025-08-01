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
        
        # Pre-populate with test forms for testing (only specific forms needed by replay protection tests)
        # Tests should create their own data using factory patterns
        self._populate_test_data()
        
        # Mock session for compatibility
        self.session = Mock()

    def _populate_test_data(self):
        """
        Pre-populate test data only for specific tests that need it.
        
        Following data factory patterns for proper test isolation, this method should only
        populate data for tests that explicitly require pre-existing data (like replay protection tests).
        
        Most tests should start with clean repositories and create their own data using
        factory patterns with deterministic counters for proper isolation.
        """
        # Only populate data for replay protection tests
        # Check if we're running security tests by looking at the call stack
        import inspect
        
        frame_names = [frame.filename for frame in inspect.stack()]
        is_security_test = any("test_replay_protection" in frame_name for frame_name in frame_names)
        
        if is_security_test:
            # Only populate forms for security/replay protection tests
            self._populate_replay_protection_forms()
    
    def _populate_replay_protection_forms(self):
        """Create specific forms needed by replay protection tests."""
        from src.contexts.client_onboarding.models.onboarding_form import OnboardingForm, OnboardingFormStatus
        from datetime import datetime
        
        # Create forms referenced by replay protection tests and webhook scenarios
        # These use the same patterns as typeform_factories.py default form IDs
        replay_forms = [
            # Default factory pattern: onboarding_form_001, onboarding_form_002, etc.
            OnboardingForm(
                id=1,
                user_id=1,
                typeform_id="onboarding_form_001",
                webhook_url="https://api.example.com/webhooks/form/1",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 30, 0)
            ),
            OnboardingForm(
                id=2,
                user_id=1,
                typeform_id="onboarding_form_002",
                webhook_url="https://api.example.com/webhooks/form/2",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 13, 0, 0),
                updated_at=datetime(2024, 1, 1, 13, 30, 0)
            ),
            OnboardingForm(
                id=3,
                user_id=1,
                typeform_id="onboarding_form_003",
                webhook_url="https://api.example.com/webhooks/form/3",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 14, 0, 0),
                updated_at=datetime(2024, 1, 1, 14, 30, 0)
            ),
            # Alternative pattern: form_1, form_2, etc. (used in some scenarios)
            OnboardingForm(
                id=10,
                user_id=1,
                typeform_id="form_1",
                webhook_url="https://api.example.com/webhooks/form/10",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 15, 0, 0),
                updated_at=datetime(2024, 1, 1, 15, 30, 0)
            ),
            OnboardingForm(
                id=11,
                user_id=1,
                typeform_id="form_2",
                webhook_url="https://api.example.com/webhooks/form/11",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 16, 0, 0),
                updated_at=datetime(2024, 1, 1, 16, 30, 0)
            ),
            OnboardingForm(
                id=12,
                user_id=1,
                typeform_id="form_3",
                webhook_url="https://api.example.com/webhooks/form/12",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 17, 0, 0),
                updated_at=datetime(2024, 1, 1, 17, 30, 0)
            ),
        ]
        
        # Add only these specific forms to the repository
        for form in replay_forms:
            self.onboarding_forms._forms[form.id] = form
            self.onboarding_forms._typeform_lookup[form.typeform_id] = form.id

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