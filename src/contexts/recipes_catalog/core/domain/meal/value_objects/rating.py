"""Value object for a user rating on a recipe."""
from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class Rating(ValueObject):
    """Value object representing a user rating on a recipe.

    Invariants:
        - Taste rating must be between 1-5
        - Convenience rating must be between 1-5
        - User ID and recipe ID must be non-empty

    Notes:
        Immutable. Equality by value (user_id, recipe_id, taste, convenience, comment).
    """
    user_id: str
    recipe_id: str
    taste: int
    convenience: int
    comment: str | None = None
