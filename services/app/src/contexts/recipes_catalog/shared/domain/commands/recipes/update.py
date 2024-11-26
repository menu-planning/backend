from typing import Any

from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateRecipe(Command):
    id: str
    updates: dict[str, Any]
    # recipe: Recipe
