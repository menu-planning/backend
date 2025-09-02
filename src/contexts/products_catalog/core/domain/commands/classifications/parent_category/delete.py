from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteParentCategory(DeleteClassification):
    """Command to delete a parent category from the catalog.
    
    Notes:
        Inherits from DeleteClassification. Removes a parent category entity
        and handles any associated product relationships.
    """
    pass
