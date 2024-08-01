from attrs import frozen

from .base_class import NameTag


@frozen
class Allergen(NameTag):
    name: str
