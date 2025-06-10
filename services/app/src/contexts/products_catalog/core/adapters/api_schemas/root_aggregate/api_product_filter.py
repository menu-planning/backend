from pydantic import BaseModel, model_validator
from src.contexts.products_catalog.core.adapters.repositories import product_repository
from src.contexts.seedwork.shared.adapters.seedwork_repository import SaGenericRepository


class ApiProductFilter(BaseModel):
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
    limit: int | None = None
    sort: str | None = "-date"
    created_at_gte: str | None = None
    created_at_lte: str | None = None
    # TODO add full text search
    # ingredients: str | None = None

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
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
        for k in values.keys():
            if SaGenericRepository.remove_postfix(k) not in allowed_filters:
                raise ValueError(f"Invalid filter: {k}")
        return values
