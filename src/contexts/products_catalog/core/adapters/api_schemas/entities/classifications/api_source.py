from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification.source import (
    Source,
)


class ApiSource(ApiClassification):
    """API schema for source entity.

    Inherits from ApiClassification with source-specific entity type.
    """

    entity_type = Source
    entity_type_name = "source"
