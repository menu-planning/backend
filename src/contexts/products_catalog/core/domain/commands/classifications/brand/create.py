from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateBrand(CreateClassification):
    """Command to create a new brand in the catalog.
    
    Notes:
        Inherits from CreateClassification. Creates a new brand entity
        for product classification and organization.
    """
    pass
