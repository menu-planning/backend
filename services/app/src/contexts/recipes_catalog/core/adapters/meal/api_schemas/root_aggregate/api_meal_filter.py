from pydantic import BaseModel, model_validator

from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
from src.contexts.recipes_catalog.core.adapters.shared.utils import parse_tags
from src.contexts.seedwork.shared.adapters.api_schemas.fields import CreatedAtValue
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiMealFilter(BaseModel):
    id: str | list[str] | None = None
    name: str | None = None
    author_id: str | list[str] | None = None
    menu_id: str | list[str] | None = None
    total_time_gte: int | None = None
    total_time_lte: int | None = None
    products: str | list[str] | None = None
    tags: str | None = None
    tags_not_exists: str | None = None
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
    calorie_density_gte: int | None = None
    calorie_density_lte: int | None = None
    carbo_percentage_gte: int | None = None
    carbo_percentage_lte: int | None = None
    protein_percentage_gte: int | None = None
    protein_percentage_lte: int | None = None
    total_fat_percentage_gte: int | None = None
    total_fat_percentage_lte: int | None = None
    weight_in_grams_gte: int | None = None
    weight_in_grams_lte: int | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    like: bool | None = None
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
        for mapper in MealRepo.filter_to_column_mappers or []:
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
