"""Event emitted when a parent category classification is created.

This event is triggered when a new parent category entity is created
in the product catalog system.
"""
from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class ParentCategoryCreated(ClassificationCreated):
    """Event emitted when a parent category classification is created.
    
    Attributes:
        name: Parent category name.
        author_id: User who created the parent category.
        description: Optional parent category description.
        classification_id: Unique identifier for the parent category.
    
    Notes:
        Emitted by: ParentCategory.create_classification(). Ordering: none.
        Inherits all attributes from ClassificationCreated.
    """
    pass
