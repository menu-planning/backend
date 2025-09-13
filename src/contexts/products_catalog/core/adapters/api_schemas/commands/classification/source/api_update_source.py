from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.source.update import (
    UpdateSource,
)


class ApiUpdateSource(ApiUpdateClassification):
    """API schema for updating a source.

    Inherits from ApiUpdateClassification with source-specific command type.
    """

    command_type = UpdateSource
