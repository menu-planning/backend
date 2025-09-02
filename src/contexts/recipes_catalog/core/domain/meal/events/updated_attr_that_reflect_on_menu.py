"""Domain event indicating a meal change that should reflect on its menu."""
from attrs import field, frozen
from src.contexts.seedwork.domain.event import Event


@frozen(kw_only=True)
class UpdatedAttrOnMealThatReflectOnMenu(Event):
    """Event emitted when a meal attribute changes and should reflect on its menu.

    Attributes:
        menu_id: ID of the menu that should be updated
        meal_id: ID of the meal that was modified
        message: Description of what changed (excluded from hash)

    Notes:
        Emitted by: Meal attribute updates
        Ordering: none
    """
    menu_id: str
    meal_id: str
    message: str = field(hash=False)

