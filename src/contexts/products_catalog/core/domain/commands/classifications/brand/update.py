from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateBrand(UpdateClassification):
    """Command to update a brand in the catalog.
    
    Notes:
        Inherits from UpdateClassification. Updates brand attributes
        atomically within a single transaction.
    """
    pass
