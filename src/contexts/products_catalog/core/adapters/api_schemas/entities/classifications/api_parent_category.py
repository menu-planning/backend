from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ParentCategory,
)


class ApiParentCategory(ApiClassification):
    entity_type = ParentCategory
    entity_type_name = "parent_category"
