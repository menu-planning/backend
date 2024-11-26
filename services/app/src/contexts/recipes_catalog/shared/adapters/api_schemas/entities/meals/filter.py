from pydantic import BaseModel, model_validator
from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    AverageRatingValue,
    CreatedAtValue,
    MonthValue,
)
from src.contexts.recipes_catalog.shared.adapters.repositories import (
    recipe as recipe_repo,
)
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiMealFilter(BaseModel):
    id: str | list[str] | None = None
    name: str | None = None
    author_id: str | list[str] | None = None
    total_time_gte: int | None = None
    total_time_lte: int | None = None
    product_name: str | None = None
    diet_types: str | list[str] | None = None
    categories: str | list[str] | None = None
    cuisines: str | list[str] | None = None
    flavors: str | list[str] | None = None
    textures: str | list[str] | None = None
    allergens_not_exists: str | list[str] | None = None
    meal_planning: str | list[str] | None = None
    privacy: Privacy | list[Privacy] | None = None
    calories_gte: int | None = None
    calories_lte: int | None = None
    protein_gte: int | None = None
    protein_lte: int | None = None
    carbohydrate_gte: int | None = None
    carbohydrate_lte: int | None = None
    total_fat_gte: int | None = None
    total_fat_lte: int | None = None
    saturated_fat_gte: int | None = None
    saturated_fat_lte: int | None = None
    trans_fat_gte: int | None = None
    trans_fat_lte: int | None = None
    sugar_gte: int | None = None
    sugar_lte: int | None = None
    sodium_gte: int | None = None
    sodium_lte: int | None = None
    calories_density_gte: int | None = None
    calories_density_lte: int | None = None
    carbo_percentage_gte: int | None = None
    carbo_percentage_lte: int | None = None
    protein_percentage_gte: int | None = None
    protein_percentage_lte: int | None = None
    total_fat_percentage_gte: int | None = None
    total_fat_percentage_lte: int | None = None
    weight_in_grams_gte: int | None = None
    weight_in_grams_lte: int | None = None
    season: str | list[str] | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    like: bool | None = None
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-created_at"
    # TODO add full text search

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        # Convert sets to lists in the output
        for key, value in data.items():
            if isinstance(value, str) and "|" in value:
                data[key] = value.split("|")
            if key == "allergens_not_exists" and isinstance(value, str):
                data[key] = value.split("|")
            if key == "season" and value is not None:
                if isinstance(value, str):
                    l = value.split("|")
                if isinstance(value, list):
                    l = value
                data[key] = [int(i) for i in l]
        return data

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in recipe_repo.RecipeRepo.filter_to_column_mappers:
            allowed_filters.extend(mapper.filter_key_to_column_name.keys())
        allowed_filters.extend(
            [
                "discarded",
                "skip",
                "limit",
                "sort",
                "created_at",
            ]
        )
        for k in values.keys():
            if SaGenericRepository.removePostfix(k) not in allowed_filters:
                raise ValueError(f"Invalid filter: {k}")
        return values
