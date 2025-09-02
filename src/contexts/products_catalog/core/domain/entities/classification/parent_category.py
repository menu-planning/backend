"""Parent category entity for product catalog classification.

Represents a parent category used for hierarchical organization
of product categories in the catalog system.
"""
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.parent_category.parent_category_created import (
    ParentCategoryCreated,
)


class ParentCategory(Classification):
    """Parent category entity for hierarchical classification.
    
    Represents a parent category used for creating hierarchical
    organization of product categories (e.g., "Food" -> "Dairy" -> "Milk").
    
    Notes:
        Inherits all functionality from Classification base class.
        Emits ParentCategoryCreated event upon creation.
    """
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "ParentCategory":
        """Create a new parent category classification.
        
        Args:
            name: Parent category name (e.g., "Food", "Electronics").
            author_id: User creating the parent category.
            description: Optional parent category description.
            
        Returns:
            New ParentCategory instance with ParentCategoryCreated event.
        """
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=ParentCategoryCreated,
            description=description,
        )
