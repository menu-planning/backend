from typing import Any

from attrs import field, frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen(kw_only=True)
class UpdatedAttrOnMealThatReflectOnMenu(Event):
    menu_id: str
    meal_id: str
    message: str = field(hash=False)
    # updates: dict[str:"attribute name", Any:"attribute value"]
