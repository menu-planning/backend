"""Domain event indicating a menu has been deleted."""
from attrs import frozen
from src.contexts.seedwork.domain.event import Event


@frozen
class MenuDeleted(Event):
    """Event emitted when a menu is deleted.

    Attributes:
        menu_id: ID of the deleted menu

    Notes:
        Emitted by: Menu.delete
        Ordering: none
    """
    menu_id: str
