from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteCategory(DeleteClassification):
    """Command to delete a product category from the catalog.
    
    Notes:
        Inherits from DeleteClassification. Removes a category entity
        and handles any associated product relationships.
    """
    pass
