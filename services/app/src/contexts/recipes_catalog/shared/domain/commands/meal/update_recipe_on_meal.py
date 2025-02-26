from typing import Any

from attrs import frozen

from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateRecipeOnMeal(Command):
    meal_id: str
    recipe_id: str
    updates: dict[str, Any]
