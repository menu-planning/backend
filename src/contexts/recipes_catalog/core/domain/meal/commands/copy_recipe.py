from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CopyRecipe(Command):
    user_id: str
    recipe_id: str
    meal_id: str
