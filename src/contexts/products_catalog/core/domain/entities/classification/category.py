"""Category entity for product catalog classification.

Represents a product category that can be used for hierarchical
organization of products in the catalog system.
"""

from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.category.category_created import (
    CategoryCreated,
)


class Category(Classification):
    """Category entity for product classification.

    Represents a product category used for hierarchical organization
    of products in the catalog system.

    Notes:
        Inherits all functionality from Classification base class.
        Emits CategoryCreated event upon creation.
    """

    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "Category":
        """Create a new category classification.

        Args:
            name: Category name (e.g., "Electronics", "Clothing").
            author_id: User creating the category.
            description: Optional category description.

        Returns:
            New Category instance with CategoryCreated event.
        """
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=CategoryCreated,
            description=description,
        )
