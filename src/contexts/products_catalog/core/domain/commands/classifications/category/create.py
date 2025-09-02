from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateCategory(CreateClassification):
    """Command to create a new product category in the catalog.
    
    Notes:
        Inherits from CreateClassification. Creates a new category entity
        for hierarchical product classification.
    """
    pass
