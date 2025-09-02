"""Domain event signaling meals were added or removed from a menu."""
from attrs import frozen
from src.contexts.seedwork.domain.event import Event


@frozen(hash=True)
class MenuMealAddedOrRemoved(Event):
    """Event emitted when meals are added or removed from a menu.

    Attributes:
        menu_id: ID of the menu that was modified
        ids_of_meals_added: Set of meal IDs that were added
        ids_of_meals_removed: Set of meal IDs that were removed

    Notes:
        Emitted by: Menu.meals setter, Menu.add_meal, Menu.remove_meals
        Ordering: none
    """
    menu_id: str
    ids_of_meals_added: frozenset[str]
    ids_of_meals_removed: frozenset[str]
