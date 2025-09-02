from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateParentCategory(CreateClassification):
    """Command to create a new parent category in the catalog.
    
    Notes:
        Inherits from CreateClassification. Creates a new parent category entity
        for hierarchical product classification structure.
    """
    pass
