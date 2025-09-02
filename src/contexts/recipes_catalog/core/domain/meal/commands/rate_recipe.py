"""Domain command to rate a recipe."""
from attrs import frozen
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class RateRecipe(Command):
    """Command to rate a recipe.

    Args:
        rating: Rating object containing user rating data
    """
    rating: Rating
