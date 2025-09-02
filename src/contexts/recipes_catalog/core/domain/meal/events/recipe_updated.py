"""Domain event indicating a recipe has been updated."""
from src.contexts.seedwork.domain.event import Event


class RecipeUpdated(Event):
    """Event emitted when a recipe is updated.

    Attributes:
        recipe_id: ID of the updated recipe

    Notes:
        Emitted by: Recipe update operations
        Ordering: none
    """
    recipe_id: str
