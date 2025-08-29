from attrs import field
from src.contexts.seedwork.shared.domain.event import Event


class RecipeCreated(Event):
    name: str
    meal_id: str | None = None
    id: str = field(factory=Event.generate_uuid)
