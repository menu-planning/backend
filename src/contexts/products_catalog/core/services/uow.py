from __future__ import annotations

from src.contexts.products_catalog.core.adapters.repositories.brand_repository import (
    BrandRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.category_repository import (
    CategoryRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.food_group_repository import (
    FoodGroupRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.parent_category_repository import (
    ParentCategoryRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.process_type_repository import (
    ProcessTypeRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.source_repository import (
    SourceRepo,
)
from src.contexts.seedwork.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    """Application transaction boundary for Products Catalog context.
    
    Usage:
        async with UnitOfWork() as uow: ...
    
    Transactions:
        Exactly-once commit. Implicit rollback on context exit if not committed.
    
    Notes:
        Repositories available: products, sources, brands, categories,
        parent_categories, food_groups, process_types. Calls must occur
        within an active context. Concurrency: async; not thread-safe.
    """
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
