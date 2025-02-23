from attrs import frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen(hash=True)
class MenuMealsChanged(Event):
    menu_id: str
    new_meals_ids: set[str]
    removed_meals_ids: set[str]
