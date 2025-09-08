"""Food group entity for product catalog classification.

Represents a food group used for nutritional classification
of food products in the catalog system.
"""

from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.food_group.food_group_created import (
    FoodGroupCreated,
)


class FoodGroup(Classification):
    """Food group entity for nutritional classification.

    Represents a food group used for nutritional classification
    of food products (e.g., "Dairy", "Grains", "Proteins").

    Notes:
        Inherits all functionality from Classification base class.
        Emits FoodGroupCreated event upon creation.
    """

    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "FoodGroup":
        """Create a new food group classification.

        Args:
            name: Food group name (e.g., "Dairy", "Grains").
            author_id: User creating the food group.
            description: Optional food group description.

        Returns:
            New FoodGroup instance with FoodGroupCreated event.
        """
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=FoodGroupCreated,
            description=description,
        )
