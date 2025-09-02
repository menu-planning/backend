from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification.parent_category import (
    ParentCategory,
)


class ApiParentCategory(ApiClassification):
    """API schema for parent category entity.
    
    Inherits from ApiClassification with parent category-specific entity type.
    """
    entity_type = ParentCategory
    entity_type_name = "parent_category"
