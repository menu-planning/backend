from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.update import (
    UpdateProcessType,
)


class ApiUpdateProcessType(ApiUpdateClassification):
    command_type = UpdateProcessType
