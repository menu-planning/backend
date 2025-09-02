from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateProcessType(CreateClassification):
    """Command to create a new process type in the catalog.
    
    Notes:
        Inherits from CreateClassification. Creates a new process type entity
        for classifying food processing methods (e.g., raw, cooked, processed).
    """
    pass
