from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class Rating(ValueObject):
    user_id: str
    recipe_id: str
    taste: int
    convenience: int
    comment: str | None = None
