from attrs import frozen

from .base_class import NameTag


@frozen(hash=True)
class Cuisine(NameTag):
    name: str
