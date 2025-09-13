from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.update import (
    UpdateProcessType,
)


class ApiUpdateProcessType(ApiUpdateClassification):
    """API schema for updating a process type.

    Inherits from ApiUpdateClassification with process type-specific command type.
    """

    command_type = UpdateProcessType
