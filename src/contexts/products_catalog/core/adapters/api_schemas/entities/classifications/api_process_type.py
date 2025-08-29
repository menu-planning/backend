from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ProcessType,
)


class ApiProcessType(ApiClassification):
    entity_type = ProcessType
    entity_type_name = "process_type"