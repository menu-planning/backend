from attrs import frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen(hash=True)
class MenuMealAddedOrRemoved(Event):
    menu_id: str
    ids_of_meals_added: set[str]
    ids_of_meals_removed: set[str]
