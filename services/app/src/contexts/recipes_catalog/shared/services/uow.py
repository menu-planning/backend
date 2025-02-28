from __future__ import annotations

from src.contexts.recipes_catalog.shared.adapters.repositories.meal.meal import \
    MealRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.menu.menu import \
    MenuRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import \
    RecipeRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.tag.recipe_tag import \
    TagRepo
from src.contexts.seedwork.shared.services.uow import \
    UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.recipes = RecipeRepo(self.session)
        self.tags = TagRepo(self.session)
        self.meals = MealRepo(self.session)
        self.menus = MenuRepo(self.session)
        return self
