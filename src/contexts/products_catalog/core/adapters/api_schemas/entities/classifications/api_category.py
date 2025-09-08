from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification.category import (
    Category,
)


class ApiCategory(ApiClassification):
    """API schema for category entity.

    Inherits from ApiClassification with category-specific entity type.
    """

    entity_type = Category
    entity_type_name = "category"
