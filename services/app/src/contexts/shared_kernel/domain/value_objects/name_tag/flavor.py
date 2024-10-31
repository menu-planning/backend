from attrs import frozen

from .base_class import NameTag


@frozen(hash=True)
class Flavor(NameTag):
    name: str
