from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateProcessType(UpdateClassification):
    """Command to update a process type in the catalog.
    
    Notes:
        Inherits from UpdateClassification. Updates process type attributes
        atomically within a single transaction.
    """
    pass
