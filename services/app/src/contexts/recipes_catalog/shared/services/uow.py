from __future__ import annotations

from src.contexts.recipes_catalog.shared.adapters.repositories.meal.meal import MealRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import (
    RecipeRepo,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe_tag import (
    RecipeTagRepo,
)
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.recipes = RecipeRepo(self.session)
        self.recipe_tags = RecipeTagRepo(self.session)
        self.meals = MealRepo(self.session)
        return self
