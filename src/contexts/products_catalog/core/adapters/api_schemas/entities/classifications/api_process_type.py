from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification.process_type import (
    ProcessType,
)


class ApiProcessType(ApiClassification):
    """API schema for process type entity.
    
    Inherits from ApiClassification with process type-specific entity type.
    """
    entity_type = ProcessType
    entity_type_name = "process_type"
