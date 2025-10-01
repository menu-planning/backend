from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from src.config.pagination_config import get_pagination_settings
from src.contexts.products_catalog.core.adapters.repositories import product_repository
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)


class ApiProductFilter(BaseModel):
    """API schema for filtering products.

    Attributes:
        id: Product identifier(s) to filter by.
        source: Source name(s) to filter by.
        name: Product name(s) to filter by.
        is_food: Filter by food status.
        barcode: Barcode(s) to filter by.
        brand: Brand name to filter by.
        category: Category name(s) to filter by.
        parent_category: Parent category name(s) to filter by.
        food_group: Food group name(s) to filter by.
        process_type: Process type name(s) to filter by.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        sort: Sort order for results.
        created_at_gte: Filter products created after this date.
        created_at_lte: Filter products created before this date.
    """

    id: str | list[str] | None = None
    source: str | list[str] | None = None
    name: str | list[str] | None = None
    is_food: bool | None = None
    barcode: str | list[str] | None = None
    brand: str | None = None
    category: str | list[str] | None = None
    parent_category: str | list[str] | None = None
    food_group: str | list[str] | None = None
    process_type: str | list[str] | None = None
    skip: int | None = None
    limit: int | None = get_pagination_settings().PRODUCTS
    sort: str | None = "-date"
    created_at_gte: str | None = None
    created_at_lte: str | None = None
    # TODO add full text search
    # ingredients: str | None = None

    @field_validator("limit")
    @classmethod
    def check_limit(cls, value: int | None) -> int:
        if value is None or value < 1:
            return 50
        return min(value, 200)

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensure that only allowed filters are used.

        Args:
            values: Filter values to validate.

        Returns:
            Validated filter values.

        Raises:
            ValidationConversionError: If invalid filter is used.
        """
        allowed_filters = []
        if product_repository.ProductRepo.filter_to_column_mappers:
            for mapper in product_repository.ProductRepo.filter_to_column_mappers:
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
        for k in values:
            if SaGenericRepository.remove_postfix(k) not in allowed_filters:
                raise ValidationConversionError(
                    f"Invalid filter: {k}",
                    schema_class=cls,
                    conversion_direction="filter_validation",
                    source_data={"filter_key": k, "allowed_filters": allowed_filters},
                )
        return values
