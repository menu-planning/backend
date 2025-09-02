from __future__ import annotations

from src.contexts.iam.core.adapters.repositories.user_repository import UserRepo
from src.contexts.seedwork.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    """IAM-specific unit-of-work wiring repositories.
    
    Extends the base UnitOfWork with IAM context repositories. Provides
    transaction boundary management for IAM domain operations.
    
    Usage:
        async with UnitOfWork(session_factory) as uow: ...
    
    Transactions:
        Exactly-once commit. Implicit rollback on context exit if not committed.
    
    Notes:
        Repositories available: users. Calls must occur within an active context.
        Concurrency: async; not thread-safe.
    """

    async def __aenter__(self):
        """Open session and attach IAM repositories.
        
        Returns:
            self: The unit-of-work instance with active session and repositories.
        
        Side Effects:
            Creates database session and initializes UserRepo.
        """
        await super().__aenter__()
        self.users = UserRepo(self.session)
        return self
