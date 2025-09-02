from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteSource(DeleteClassification):
    """Command to delete a data source from the catalog.
    
    Notes:
        Inherits from DeleteClassification. Removes a data source entity
        and handles any associated product relationships.
    """
    pass
