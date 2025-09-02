"""Domain event indicating a meal has been deleted."""
from attrs import frozen
from src.contexts.seedwork.domain.event import Event


@frozen(kw_only=True)
class MealDeleted(Event):
    """Event emitted when a meal is deleted.

    Attributes:
        menu_id: ID of the menu the meal belonged to
        meal_id: ID of the deleted meal

    Notes:
        Emitted by: Meal.delete
        Ordering: none
    """
    menu_id: str
    meal_id: str
