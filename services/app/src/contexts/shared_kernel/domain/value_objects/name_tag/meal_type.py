from attrs import frozen

from .base_class import NameTag


@frozen(hash=True)
class MealType(NameTag):
    """
    The MealType represents the type of meal. For example, breakfast,
    lunch, dinner, etc.

    """

    name: str
