from attrs import frozen

from .base_class import NameTag


@frozen
class Texture(NameTag):
    name: str
