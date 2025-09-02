"""Unit of Work wiring for recipes catalog services."""
from __future__ import annotations

from src.contexts.recipes_catalog.core.adapters.client.repositories.client_repository import (
    ClientRepo,
)
from src.contexts.recipes_catalog.core.adapters.client.repositories.menu_repository import (
    MenuRepo,
)
from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import (
    MealRepo,
)
from src.contexts.recipes_catalog.core.adapters.meal.repositories.recipe_repository import (
    RecipeRepo,
)
from src.contexts.seedwork.services.uow import UnitOfWork as SeedUnitOfWork
from src.contexts.shared_kernel.adapters.repositories.tags.tag_repository import TagRepo


class UnitOfWork(SeedUnitOfWork):
    """Bind repositories for recipes catalog within a transactional context."""
    async def __aenter__(self):
        await super().__aenter__()
        self.recipes = RecipeRepo(self.session)
        self.tags = TagRepo(self.session)
        self.meals = MealRepo(self.session)
        self.menus = MenuRepo(self.session)
        self.clients = ClientRepo(self.session)
        return self
