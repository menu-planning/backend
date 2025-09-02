from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateSource(CreateClassification):
    """Command to create a new data source in the catalog.
    
    Notes:
        Inherits from CreateClassification. Creates a new data source entity
        for tracking product data origins and quality.
    """
    pass
