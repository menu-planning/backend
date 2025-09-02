from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteProcessType(DeleteClassification):
    """Command to delete a process type from the catalog.
    
    Notes:
        Inherits from DeleteClassification. Removes a process type entity
        and handles any associated product relationships.
    """
    pass
