from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteBrand(DeleteClassification):
    """Command to delete a brand from the catalog.
    
    Notes:
        Inherits from DeleteClassification. Removes a brand entity
        and handles any associated product relationships.
    """
    pass
