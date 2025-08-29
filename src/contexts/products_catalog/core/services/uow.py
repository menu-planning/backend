from __future__ import annotations

from src.contexts.products_catalog.core.adapters.repositories import (
    BrandRepo,
    CategoryRepo,
    FoodGroupRepo,
    ParentCategoryRepo,
    ProcessTypeRepo,
    ProductRepo,
    SourceRepo,
)
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.products = ProductRepo(self.session)
        self.sources = SourceRepo(self.session)
        self.brands = BrandRepo(self.session)
        self.categories = CategoryRepo(self.session)
        self.parent_categories = ParentCategoryRepo(self.session)
        self.food_groups = FoodGroupRepo(self.session)
        self.process_types = ProcessTypeRepo(self.session)
        return self
