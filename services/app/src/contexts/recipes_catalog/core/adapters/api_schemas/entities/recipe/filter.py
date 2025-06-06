from typing import Any, Dict
from pydantic import Field, model_validator

from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.fields import AverageRatingValue
from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseApiModel
from src.contexts.recipes_catalog.core.adapters.api_schemas.utils import parse_tags
from src.contexts.recipes_catalog.core.adapters.repositories.recipe.recipe import RecipeRepo
from src.contexts.seedwork.shared.adapters.api_schemas.fields import CreatedAtValue
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiRecipeFilter(BaseApiModel[Any, Any]):
    """
    A Pydantic model representing and validating recipe filter parameters.
    
    This model is used for input validation and serialization of filter
    parameters in API requests.

    Attributes:
        id (str | list[str] | None): Filter by recipe ID(s)
        name (str | None): Filter by recipe name
        author_id (str | list[str] | None): Filter by author ID(s)
        meal_id (str | list[str] | None): Filter by meal ID(s)
        total_time_gte (int | None): Filter by minimum total time
        total_time_lte (int | None): Filter by maximum total time
        products (str | list[str] | None): Filter by product ID(s)
        tags (str | None): Filter by tags (comma-separated or pipe-separated)
        tags_not_exists (str | None): Filter by non-existent tags
        privacy (Privacy | list[Privacy] | None): Filter by privacy setting(s)
        calories_gte (float | None): Filter by minimum calories
        calories_lte (float | None): Filter by maximum calories
        protein_gte (float | None): Filter by minimum protein
        protein_lte (float | None): Filter by maximum protein
        carbohydrate_gte (float | None): Filter by minimum carbohydrate
        carbohydrate_lte (float | None): Filter by maximum carbohydrate
        total_fat_gte (float | None): Filter by minimum total fat
        total_fat_lte (float | None): Filter by maximum total fat
        saturated_fat_gte (float | None): Filter by minimum saturated fat
        saturated_fat_lte (float | None): Filter by maximum saturated fat
        trans_fat_gte (float | None): Filter by minimum trans fat
        trans_fat_lte (float | None): Filter by maximum trans fat
        sugar_gte (float | None): Filter by minimum sugar
        sugar_lte (float | None): Filter by maximum sugar
        sodium_gte (float | None): Filter by minimum sodium
        sodium_lte (float | None): Filter by maximum sodium
        calorie_density_gte (float | None): Filter by minimum calorie density
        calorie_density_lte (float | None): Filter by maximum calorie density
        carbo_percentage_gte (float | None): Filter by minimum carbohydrate percentage
        carbo_percentage_lte (float | None): Filter by maximum carbohydrate percentage
        protein_percentage_gte (float | None): Filter by minimum protein percentage
        protein_percentage_lte (float | None): Filter by maximum protein percentage
        total_fat_percentage_gte (float | None): Filter by minimum total fat percentage
        total_fat_percentage_lte (float | None): Filter by maximum total fat percentage
        weight_in_grams_gte (int | None): Filter by minimum weight
        weight_in_grams_lte (int | None): Filter by maximum weight
        created_at_gte (CreatedAtValue): Filter by minimum creation date
        created_at_lte (CreatedAtValue): Filter by maximum creation date
        average_taste_rating_gte (AverageRatingValue): Filter by minimum taste rating
        average_convenience_rating_gte (AverageRatingValue): Filter by minimum convenience rating
        skip (int | None): Number of records to skip
        limit (int | None): Maximum number of records to return
        sort (str | None): Sort field and direction
    """

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
    created_at_gte: CreatedAtValue = None
    created_at_lte: CreatedAtValue = None
    average_taste_rating_gte: AverageRatingValue = None
    average_convenience_rating_gte: AverageRatingValue = None
    skip: int | None = None
    limit: int | None = Field(default=100, ge=1, le=1000)
    sort: str | None = Field(default="-created_at")
    # TODO add full text search

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """Convert the model to a dictionary, handling special cases for tags and pipe-separated values."""
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if key == "tags" or key == "tags_not_exists":
                data[key] = parse_tags(value)
            elif isinstance(value, str) and "|" in value:
                data[key] = value.split("|")
        return data

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in RecipeRepo.filter_to_column_mappers or []:
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
