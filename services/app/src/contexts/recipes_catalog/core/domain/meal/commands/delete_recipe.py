from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteRecipe(Command):
    recipe_id: str
