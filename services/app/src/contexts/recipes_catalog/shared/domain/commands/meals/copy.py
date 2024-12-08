from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CopyMeal(Command):
    user_id: str
    meal_id: str
