"""Event emitted when a category classification is created.

This event is triggered when a new category entity is created
in the product catalog system.
"""
from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class CategoryCreated(ClassificationCreated):
    """Event emitted when a category classification is created.
    
    Attributes:
        name: Category name.
        author_id: User who created the category.
        description: Optional category description.
        classification_id: Unique identifier for the category.
    
    Notes:
        Emitted by: Category.create_classification(). Ordering: none.
        Inherits all attributes from ClassificationCreated.
    """
    pass
