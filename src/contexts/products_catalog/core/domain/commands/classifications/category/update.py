from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateCategory(UpdateClassification):
    """Command to update a product category in the catalog.
    
    Notes:
        Inherits from UpdateClassification. Updates category attributes
        atomically within a single transaction.
    """
    pass
