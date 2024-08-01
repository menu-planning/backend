from __future__ import annotations

from src.contexts.products_catalog.shared.adapters.repositories import (
    BrandRepo,
    CategoryRepo,
    FoodGroupRepo,
    ParentCategoryRepo,
    ProcessTypeRepo,
    ProductRepo,
    SourceRepo,
)
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork
from src.contexts.shared_kernel.adapters.repositories.allergen import AllergenRepo
from src.contexts.shared_kernel.adapters.repositories.diet_type import DietTypeRepo


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
        self.diet_types = DietTypeRepo(self.session)
        self.allergens = AllergenRepo(self.session)
        return self
