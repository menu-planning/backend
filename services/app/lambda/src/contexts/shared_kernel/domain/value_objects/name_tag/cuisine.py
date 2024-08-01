from attrs import frozen

from .base_class import NameTag


@frozen
class Cuisine(NameTag):
    name: str
