from __future__ import annotations

from src.contexts.food_tracker.shared.adapters.repositories.houses import HousesRepo
from src.contexts.food_tracker.shared.adapters.repositories.items import ItemsRepo
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.houses = HousesRepo(self.session)
        self.items = ItemsRepo(self.session)
        return self
