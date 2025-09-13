from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.source.create import (
    CreateSource,
)


class ApiCreateSource(ApiCreateClassification):
    """API schema for creating a new source.

    Inherits from ApiCreateClassification with source-specific command type.
    """

    command_type = CreateSource
