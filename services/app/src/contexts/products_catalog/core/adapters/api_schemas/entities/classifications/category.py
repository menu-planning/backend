from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification import Category


class ApiCategory(ApiClassification):
    entity_type = Category