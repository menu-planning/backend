from typing import Any

from attrs import frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen(kw_only=True, hash=True)
class MealDeleted(Event):
    menu_id: str
    meal_id: str
