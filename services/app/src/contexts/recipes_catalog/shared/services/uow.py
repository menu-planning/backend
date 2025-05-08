from __future__ import annotations

from src.contexts.recipes_catalog.shared.adapters.repositories.meal.meal import \
    MealRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.menu.menu import \
    MenuRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.client.client import \
    ClientRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import \
    RecipeRepo
from src.contexts.seedwork.shared.services.uow import \
    UnitOfWork as SeedUnitOfWork
from src.contexts.shared_kernel.adapters.repositories.tags.tag import TagRepo


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.recipes = RecipeRepo(self.session)
        self.tags = TagRepo(self.session)
        self.meals = MealRepo(self.session)
        self.menus = MenuRepo(self.session)
        self.clients = ClientRepo(self.session)
        return self
