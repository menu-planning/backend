from __future__ import annotations

from src.contexts.iam.core.adapters.repositories.user_repository import UserRepo
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.users = UserRepo(self.session)
        return self
