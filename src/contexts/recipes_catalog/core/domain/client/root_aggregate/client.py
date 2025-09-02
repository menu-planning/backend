"""Client aggregate for the recipes catalog domain."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
)
from src.contexts.seedwork.domain.entity import Entity
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.tag import Tag

if TYPE_CHECKING:
    from src.contexts.seedwork.domain.event import Event


class Client(Entity):
    """Client aggregate root owning menus and profile/contact data.

    Clients aggregate personal data and a collection of menus. Mutations occur
    through methods on this aggregate to keep versioning and invariants.
    """
    def __init__(
        self,
        *,
        entity_id: str,
        author_id: str,
        profile: Profile,
        contact_info: ContactInfo | None = None,
        address: Address | None = None,
        tags: set[Tag] | None = None,
        menus: list[Menu] | None = None,
        notes: str | None = None,
        onboarding_data: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Client."""
        super().__init__(
            entity_id=entity_id,
            discarded=discarded,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._author_id = author_id
        self._profile = profile
        self._contact_info = contact_info
        self._address = address if address else None
        self._tags = tags if tags else set()
        self._contact_info = contact_info
        self._menus = menus if menus else []
        self._notes = notes
        self._onboarding_data = onboarding_data
        self.events: list[Event] = []

    @classmethod
    def create_client(
        cls,
        *,
        author_id: str,
        profile: Profile,
        contact_info: ContactInfo,
        tags: set[Tag] | None = None,
        address: Address | None = None,
        notes: str | None = None,
        onboarding_data: dict[str, Any] | None = None,
    ) -> "Client":
        client_id = uuid.uuid4().hex
        return cls(
            entity_id=client_id,
            author_id=author_id,
            profile=profile,
            contact_info=contact_info,
            address=address,
            tags=tags,
            notes=notes,
            onboarding_data=onboarding_data,
        )

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def profile(self) -> Profile:
        self._check_not_discarded()
        return self._profile

    @profile.setter
    def profile(self, profile: Profile) -> None:
        self._check_not_discarded()
        if self._profile != profile:
            self._profile = profile
            self._increment_version()

    @property
    def contact_info(self) -> ContactInfo | None:
        self._check_not_discarded()
        return self._contact_info

    @contact_info.setter
    def contact_info(self, contact_info: ContactInfo) -> None:
        self._check_not_discarded()
        if self._contact_info != contact_info:
            self._contact_info = contact_info
            self._increment_version()

    @property
    def address(self) -> Address | None:
        self._check_not_discarded()
        return self._address

    @address.setter
    def address(self, address: Address) -> None:
        self._check_not_discarded()
        if self._address != address:
            self._address = address
            self._increment_version()

    @property
    def menus(self) -> list[Menu]:
        self._check_not_discarded()
        return [menu for menu in self._menus if not menu.discarded]

    def create_menu(
        self,
        *,
        description: str | None = None,
        tags: frozenset[Tag] | None = None,
        menu_id: str,
    ) -> None:
        """Create and append a new `Menu` for this client."""
        self._check_not_discarded()
        menu = Menu.create_menu(
            author_id=self._author_id,
            client_id=self.id,
            description=description,
            tags=tags,
            menu_id=menu_id,
        )
        self._menus.append(menu)
        self._increment_version()

    def delete_menu(self, menu: Menu) -> None:
        """Remove a menu from the client and soft-delete it if present."""
        self._check_not_discarded()
        if menu.discarded or menu not in self._menus:
            return
        self._menus.remove(menu)
        menu._discard()
        self._increment_version()

    @property
    def discarded_menus(self) -> list[Menu]:
        self._check_not_discarded()
        return [menu for menu in self._menus if menu.discarded]

    @property
    def notes(self) -> str | None:
        self._check_not_discarded()
        return self._notes

    @notes.setter
    def notes(self, notes: str) -> None:
        self._check_not_discarded()
        if self._notes != notes:
            self._notes = notes
            self._increment_version()

    @property
    def onboarding_data(self) -> dict[str, Any] | None:
        self._check_not_discarded()
        return self._onboarding_data

    @onboarding_data.setter
    def onboarding_data(self, onboarding_data: dict[str, Any] | None) -> None:
        self._check_not_discarded()
        if self._onboarding_data != onboarding_data:
            self._onboarding_data = onboarding_data
            self._increment_version()

    @property
    def tags(self) -> set[Tag]:
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: set[Tag]) -> None:
        self._check_not_discarded()
        for tag in value:
            Client.check_rule(
                AuthorIdOnTagMustMachRootAggregateAuthor(tag, self),
            )
        self._tags = value
        self._increment_version()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(client_id={self.id}, client_name={self.profile.name})"
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
