"""Domain command to delete a meal aggregate."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteMeal(Command):
    """Command to delete an existing meal.

    Args:
        meal_id: ID of the meal to delete
    """
    meal_id: str
