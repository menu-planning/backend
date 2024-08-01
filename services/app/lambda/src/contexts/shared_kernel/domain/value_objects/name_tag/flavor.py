from attrs import frozen

from .base_class import NameTag


@frozen
class Flavor(NameTag):
    name: str
