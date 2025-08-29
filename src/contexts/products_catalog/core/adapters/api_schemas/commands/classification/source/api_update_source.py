from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.source.update import (
    UpdateSource,
)


class ApiUpdateSource(ApiUpdateClassification):
    command_type = UpdateSource
