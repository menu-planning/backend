import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class RecipeCreated(Event):
    author_id: str
    name: str
    recipe_id: str = field(factory=lambda: uuid.uuid4().hex)
