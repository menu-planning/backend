"""Event emitted when a brand classification is created.

This event is triggered when a new brand entity is created
in the product catalog system.
"""
from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class BrandCreated(ClassificationCreated):
    """Event emitted when a brand classification is created.
    
    Attributes:
        name: Brand name.
        author_id: User who created the brand.
        description: Optional brand description.
        classification_id: Unique identifier for the brand.
    
    Notes:
        Emitted by: Brand.create_classification(). Ordering: none.
        Inherits all attributes from ClassificationCreated.
    """
    pass
