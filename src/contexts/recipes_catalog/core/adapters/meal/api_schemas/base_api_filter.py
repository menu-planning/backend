from typing import Any

from pydantic import BaseModel, Field, model_validator
from src.contexts.recipes_catalog.core.adapters.shared.parse_tags import parse_tags
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    CreatedAtValue,
)
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    SaGenericRepository,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class BaseMealApiFilter(BaseModel):
    """
    Base API filter schema with comprehensive filtering capabilities.

    This class provides common filtering options that can be extended by specific
    filter implementations. It supports various filter types including basic
    identification, time constraints, tags, privacy controls, and pagination.

    Filter Syntax:
    - Single values: "value"
    - Multiple values: "value1|value2|value3" (automatically converted to lists)
    - Tag filters: "key:value1|value2,key2:value3" (parsed into structured format)

    Examples:
        # Filter by multiple IDs
        id: "item1|item2|item3"

        # Filter by multiple authors
        author_id: "user1|user2"

        # Filter by tags with key-value pairs
        tags: "cuisine:italian|mediterranean,meal_type:breakfast|lunch"
        tags_not_exists: "allergen:dairy|nuts"

        # Filter by time constraints
        total_time_gte: 30
        total_time_lte: 60

        # Filter by nutritional ranges
        calories_gte: 200
        calories_lte: 500
    """

    # Basic identification filters
    id: str | list[str] | None = None
    name: str | None = None
    author_id: str | list[str] | None = None

    # Time-based filters (in minutes)
    total_time_gte: int | None = None
    total_time_lte: int | None = None

    # Product and tag filters
    products: str | list[str] | None = None
    tags: str | None = None
    tags_not_exists: str | None = None

    # Privacy and access control
    privacy: Privacy | list[Privacy] | None = None

    # Nutritional value filters (in grams, calories, or percentages)
    calories_gte: float | int | None = None
    calories_lte: float | int | None = None
    protein_gte: float | int | None = None
    protein_lte: float | int | None = None
    carbohydrate_gte: float | int | None = None
    carbohydrate_lte: float | int | None = None
    total_fat_gte: float | int | None = None
    total_fat_lte: float | int | None = None
    saturated_fat_gte: float | int | None = None
    saturated_fat_lte: float | int | None = None
    trans_fat_gte: float | int | None = None
    trans_fat_lte: float | int | None = None
    sugar_gte: float | int | None = None
    sugar_lte: float | int | None = None
    sodium_gte: float | int | None = None
    sodium_lte: float | int | None = None
    calorie_density_gte: float | int | None = None
    calorie_density_lte: float | int | None = None
    carbo_percentage_gte: float | int | None = None
    carbo_percentage_lte: float | int | None = None
    protein_percentage_gte: float | int | None = None
    protein_percentage_lte: float | int | None = None
    total_fat_percentage_gte: float | int | None = None
    total_fat_percentage_lte: float | int | None = None

    # Weight and portion filters
    weight_in_grams_gte: int | None = None
    weight_in_grams_lte: int | None = None

    # Temporal filters
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None

    # Pagination and sorting
    skip: int | None = None
    limit: int | None = Field(default=100, ge=1, le=1000)
    sort: str | None = Field(default="-created_at")

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        """
        Custom model dump that processes special filter formats.

        This method handles:
        1. Tag filters: Converts "key:value1|value2,key2:value3" format to structured
        data
        2. String lists: Converts "value1|value2|value3" format to actual lists

        Returns:
            dict: Processed filter data ready for database queries
        """
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if key in ["tags", "tags_not_exists"]:
                # Parse tag filters from "key:value1|value2,key2:value3" format
                # This converts the string into a structured format for tag filtering
                data[key] = parse_tags(value)
            elif isinstance(value, str) and "|" in value:
                # Convert pipe-separated strings to lists
                # Example: "item1|item2|item3" becomes ["item1", "item2", "item3"]
                data[key] = value.split("|")
        return data

    @model_validator(mode="before")
    @classmethod
    def validate_filter_keys(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Base validator for filter keys.

        This validator ensures that basic filter validation is performed.
        Subclasses should override this method to add repository-specific validation.

        Args:
            values: The filter values to validate

        Returns:
            dict: The validated filter values
        """
        # Basic validation - ensure required fields are present if needed
        # Subclasses can extend this with more specific validation
        return values

    def get_allowed_filters(self) -> list[str]:
        """
        Get the list of allowed filter keys for this filter.

        This method should be overridden by subclasses to provide
        repository-specific allowed filters.

        Returns:
            list[str]: List of allowed filter keys
        """
        return [
            "discarded",
            "skip",
            "limit",
            "sort",
            "created_at",
            "tags",
            "tags_not_exists",
        ]

    def validate_repository_filters(
        self, values: dict[str, Any], repo_mappers: list | None
    ) -> dict[str, Any]:
        """
        Validate that only allowed filters are used.

        This method ensures that all provided filter keys are supported
        by the underlying repository layer, preventing invalid filter errors.

        Args:
            values: The filter values to validate
            repo_mappers: Repository filter mappers to check against

        Returns:
            dict: The validated filter values

        Raises:
            ValueError: If an invalid filter key is provided
        """
        allowed_filters = self.get_allowed_filters()

        if repo_mappers:
            for mapper in repo_mappers:
                if hasattr(mapper, "filter_key_to_column_name"):
                    allowed_filters.extend(mapper.filter_key_to_column_name.keys())

        for key in values:
            if SaGenericRepository.remove_postfix(key) not in allowed_filters:
                error_message = f"Invalid filter: {key}"
                raise ValueError(error_message)

        return values
