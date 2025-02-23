from attrs import frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen
class MenuDeleted(Event):
    menu_id: str
