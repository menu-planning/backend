"""Domain command to copy an existing meal to another menu."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class CopyMeal(Command):
    """Command to copy an existing meal to another menu.

    Args:
        id_of_user_coping_meal: ID of the user copying the meal
        meal_id: ID of the meal to copy
        id_of_target_menu: ID of the target menu (optional, creates new if not provided)
    """
    id_of_user_coping_meal: str
    meal_id: str
    id_of_target_menu: str | None = None
