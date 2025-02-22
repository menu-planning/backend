from typing import Any

from attrs import frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen(kw_only=True, hash=True)
class UpdatedAttrOnMealThatReflectOnMenu(Event):
    menu_id: str
    meal_id: str
    # updates: dict[str:"attribute name", Any:"attribute value"]
