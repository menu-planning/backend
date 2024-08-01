from __future__ import annotations

from src.contexts.recipes_catalog.shared.adapters.repositories import (
    CategoryRepo,
    MealPlanningRepo,
    RecipeRepo,
)
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork
from src.contexts.shared_kernel.adapters.repositories.allergen import AllergenRepo
from src.contexts.shared_kernel.adapters.repositories.cuisine import CuisineRepo
from src.contexts.shared_kernel.adapters.repositories.diet_type import DietTypeRepo
from src.contexts.shared_kernel.adapters.repositories.flavor import FlavorRepo
from src.contexts.shared_kernel.adapters.repositories.texture import TextureRepo


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.recipes = RecipeRepo(self.session)
        self.diet_types = DietTypeRepo(self.session)
        self.categories = CategoryRepo(self.session)
        self.cuisines = CuisineRepo(self.session)
        self.flavors = FlavorRepo(self.session)
        self.meal_plannings = MealPlanningRepo(self.session)
        self.textures = TextureRepo(self.session)
        self.allergens = AllergenRepo(self.session)
        return self
