from attrs import frozen
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class RateRecipe(Command):
    rating: Rating
