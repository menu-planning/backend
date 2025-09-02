from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateParentCategory(UpdateClassification):
    """Command to update a parent category in the catalog.
    
    Notes:
        Inherits from UpdateClassification. Updates parent category attributes
        atomically within a single transaction.
    """
    pass
