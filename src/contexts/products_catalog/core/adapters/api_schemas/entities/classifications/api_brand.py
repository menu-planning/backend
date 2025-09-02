from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification.brand import (
    Brand,
)


class ApiBrand(ApiClassification):
    """API schema for brand entity.
    
    Inherits from ApiClassification with brand-specific entity type.
    """
    entity_type = Brand
    entity_type_name = "brand"
