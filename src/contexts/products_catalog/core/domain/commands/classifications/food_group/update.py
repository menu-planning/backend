from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateFoodGroup(UpdateClassification):
    """Command to update a food group in the catalog.
    
    Notes:
        Inherits from UpdateClassification. Updates food group attributes
        atomically within a single transaction.
    """
    pass
