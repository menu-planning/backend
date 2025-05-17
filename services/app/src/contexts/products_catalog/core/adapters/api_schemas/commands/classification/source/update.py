from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.source.update import (
    UpdateSource,
)


class ApiUpdateSource(ApiUpdateClassification):
    command_type = UpdateSource
