from attrs import frozen

from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CopyMeal(Command):
    id_of_user_coping_meal: str
    meal_id: str
    id_of_target_menu: str | None = None
