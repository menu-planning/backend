from typing import Any

from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateMeal(Command):
    meal_id: str
    updates: dict[str, Any]
