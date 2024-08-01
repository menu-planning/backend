from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command

from .create import CreateRecipe


@frozen(kw_only=True)
class AddRecipeBulk(Command):
    list_of_add_recipe_cmds: list[CreateRecipe]
