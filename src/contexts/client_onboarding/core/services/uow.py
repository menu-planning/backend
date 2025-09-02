"""Client onboarding unit of work for database session management.

Manages database sessions and repositories for client onboarding operations
with async session lifecycle and repository access.
"""

from __future__ import annotations

from src.contexts.client_onboarding.core.adapters.repositories.form_response_repository import (
    FormResponseRepo,
)
from src.contexts.client_onboarding.core.adapters.repositories.onboarding_form_repository import (
    OnboardingFormRepo,
)
from src.contexts.seedwork.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    """Unit of Work for client onboarding context.

    Provides access to onboarding form and form response repositories
    with async session management and transaction boundaries.

    Usage:
        async with UnitOfWork() as uow:
            form = await uow.onboarding_forms.get_by_id(form_id)
            await uow.commit()
    """

    async def __aenter__(self):
        """Initialize unit of work with repository access."""
        await super().__aenter__()
        self.onboarding_forms = OnboardingFormRepo(self.session)
        self.form_responses = FormResponseRepo(self.session)
        return self
