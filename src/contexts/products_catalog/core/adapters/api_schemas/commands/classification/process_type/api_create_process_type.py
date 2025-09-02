from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.create import (
    CreateProcessType,
)


class ApiCreateProcessType(ApiCreateClassification):
    """API schema for creating a new process type.
    
    Inherits from ApiCreateClassification with process type-specific command type.
    """
    command_type = CreateProcessType
