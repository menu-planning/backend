from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_item import MenuItem
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.enums import Weekday
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateMenu(Command):
    author_id: str
    client_id: str | None = None
    description: str | None = None
    items: dict[tuple[int, Weekday, MealType], MenuItem] | None = None
    tags: set[Tag] | None = None
