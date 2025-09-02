from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateSource(UpdateClassification):
    """Command to update a data source in the catalog.
    
    Notes:
        Inherits from UpdateClassification. Updates data source attributes
        atomically within a single transaction.
    """
    pass
