from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateFoodGroup(CreateClassification):
    """Command to create a new food group in the catalog.
    
    Notes:
        Inherits from CreateClassification. Creates a new food group entity
        for nutritional classification of food products.
    """
    pass
