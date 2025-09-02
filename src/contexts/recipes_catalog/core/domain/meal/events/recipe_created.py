"""Domain event indicating a recipe has been created."""
from attrs import field
from src.contexts.seedwork.domain.event import Event


class RecipeCreated(Event):
    """Event emitted when a recipe is created.

    Attributes:
        name: Name of the created recipe
        meal_id: ID of the meal the recipe belongs to (optional)
        id: Unique identifier for the event

    Notes:
        Emitted by: Recipe creation
        Ordering: none
    """
    name: str
    meal_id: str | None = None
    id: str = field(factory=Event.generate_uuid)
