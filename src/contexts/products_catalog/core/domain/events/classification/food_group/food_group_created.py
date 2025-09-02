"""Event emitted when a food group classification is created.

This event is triggered when a new food group entity is created
in the product catalog system.
"""
from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class FoodGroupCreated(ClassificationCreated):
    """Event emitted when a food group classification is created.
    
    Attributes:
        name: Food group name.
        author_id: User who created the food group.
        description: Optional food group description.
        classification_id: Unique identifier for the food group.
    
    Notes:
        Emitted by: FoodGroup.create_classification(). Ordering: none.
        Inherits all attributes from ClassificationCreated.
    """
    pass
