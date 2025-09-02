from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteFoodGroup(DeleteClassification):
    """Command to delete a food group from the catalog.
    
    Notes:
        Inherits from DeleteClassification. Removes a food group entity
        and handles any associated product relationships.
    """
    pass
