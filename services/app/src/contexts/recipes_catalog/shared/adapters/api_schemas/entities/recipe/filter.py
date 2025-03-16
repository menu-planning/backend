from pydantic import BaseModel, model_validator

from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    AverageRatingValue,
    CreatedAtValue,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.utils import parse_tags
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import RecipeRepo
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiRecipeFilter(BaseModel):
    id: str | list[str] | None = None
    name: str | None = None
    author_id: str | list[str] | None = None
    meal_id: str | list[str] | None = None
    total_time_gte: int | None = None
    total_time_lte: int | None = None
    products: str | list[str] | None = None
    tags: str | None = None
    tags_not_exists: str | None = None
    privacy: Privacy | list[Privacy] | None = None
    calories_gte: float | None = None
    calories_lte: float | None = None
    protein_gte: float | None = None
    protein_lte: float | None = None
    carbohydrate_gte: float | None = None
    carbohydrate_lte: float | None = None
    total_fat_gte: float | None = None
    total_fat_lte: float | None = None
    saturated_fat_gte: float | None = None
    saturated_fat_lte: float | None = None
    trans_fat_gte: float | None = None
    trans_fat_lte: float | None = None
    sugar_gte: float | None = None
    sugar_lte: float | None = None
    sodium_gte: float | None = None
    sodium_lte: float | None = None
    calorie_density_gte: float | None = None
    calorie_density_lte: float | None = None
    carbo_percentage_gte: float | None = None
    carbo_percentage_lte: float | None = None
    protein_percentage_gte: float | None = None
    protein_percentage_lte: float | None = None
    total_fat_percentage_gte: float | None = None
    total_fat_percentage_lte: float | None = None
    weight_in_grams_gte: int | None = None
    weight_in_grams_lte: int | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    average_taste_rating_gte: AverageRatingValue | None = None
    average_convenience_rating_gte: AverageRatingValue | None = None
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-created_at"
    # TODO add full text search

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if key == "tags" or key == "tags_not_exists":
                data[key] = parse_tags(value)
            elif isinstance(value, str) and "|" in value:
                data[key] = value.split("|")
        return data

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in RecipeRepo.filter_to_column_mappers:
            allowed_filters.extend(mapper.filter_key_to_column_name.keys())
        allowed_filters.extend(
            [
                "discarded",
                "skip",
                "limit",
                "sort",
                "created_at",
                "tags",
                "tags_not_exists",
            ]
        )
        for k in values.keys():
            if SaGenericRepository.remove_postfix(k) not in allowed_filters:
                raise ValueError(f"Invalid filter: {k}")
        return values
