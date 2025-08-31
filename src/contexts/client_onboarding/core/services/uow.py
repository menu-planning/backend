"""
Client Onboarding Unit of Work

Manages database sessions and repositories for client onboarding operations.
"""

from __future__ import annotations

from src.contexts.client_onboarding.core.adapters.repositories import (
    FormResponseRepo,
    OnboardingFormRepo,
)
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    """
    Unit of Work for client onboarding context.
    
    Provides access to onboarding form and form response repositories
    with async session management.
    """

    async def __aenter__(self):
        await super().__aenter__()
        self.onboarding_forms = OnboardingFormRepo(self.session)
        self.form_responses = FormResponseRepo(self.session)
        return self
