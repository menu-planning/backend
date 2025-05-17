from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ProcessType,
)


class ApiProcessType(ApiClassification):
    entity_type = ProcessType