"""Client aggregate for the shopping list domain."""

from datetime import datetime

from src.contexts.seedwork.domain.entity import Entity
from src.contexts.seedwork.domain.event import Event
from src.contexts.shopping_list.core.domain.rules import MaxNumberOfShoppingLists
from src.contexts.shopping_list.core.domain.value_objects.shopping_list import ShoppingList


class Client(Entity):
    """Client aggregate root owning menus and profile/contact data.

    Clients aggregate personal data and a collection of menus. Mutations occur
    through methods on this aggregate to keep versioning and invariants.
    """

    def __init__(
        self,
        *,
        id: str,
        shopping_lists: list[ShoppingList],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Client."""
        super().__init__(
            id=id,
            discarded=discarded,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._shopping_list = shopping_lists
        self.events: list[Event] = []

    @classmethod
    def create_client(
        cls,
        *,
        client_id: str,
        shopping_lists: list[ShoppingList],
    ) -> "Client":
        return cls(
            id=client_id,
            shopping_lists=shopping_lists,
        )

    @property
    def shopping_list(self) -> list[ShoppingList]:
        self._check_not_discarded()
        return self._shopping_list

    @shopping_list.setter
    def shopping_list(self, shopping_list: list[ShoppingList]) -> None:
        self._check_not_discarded()
        Client.check_rule(
            MaxNumberOfShoppingLists(self),
        )
        if self._shopping_list != shopping_list:
            self._shopping_list = shopping_list
            self._increment_version()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(client_id={self.id}, number_of_shopping_lists={len(self.shopping_list)})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Client):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)

    def delete(self) -> None:
        self._check_not_discarded()
        self._discard()
