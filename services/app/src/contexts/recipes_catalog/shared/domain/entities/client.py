from datetime import datetime
import uuid
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.domain.rules import AuthorIdOnTagMustMachRootAggregateAuthor
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.value_objects.tag import Tag

class Client(Entity):
    def __init__(
        self,
        *,
        id: str,
        author_id: str,
        profile: Profile,
        contact_info: ContactInfo | None = None,
        address: Address | None = None,
        tags: set[Tag] | None = None,
        menus: list[Menu] | None = None,
        notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Client."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._author_id = author_id
        self._profile = profile
        self._contact_info = contact_info
        self._address = address if address else None
        self._tags = tags if tags else set()
        self._contact_info = contact_info
        self._menus = menus if menus else []
        self._notes = notes
        self._created_at = created_at
        self._updated_at = updated_at
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
    ) -> "Client":
        client_id = uuid.uuid4().hex
        client = cls(
            id=client_id,
            author_id=author_id,
            profile=profile,
            contact_info=contact_info,
            address=address,
            tags=tags,
            notes=notes,
        )
        return client
    
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
        if (self._profile != profile):
            self._profile = profile
            self._increment_version()

    @property
    def contact_info(self) -> ContactInfo:
        self._check_not_discarded()
        return self._contact_info
    
    @contact_info.setter
    def contact_info(self, contact_info: ContactInfo) -> None:
        self._check_not_discarded()
        if (self._contact_info != contact_info):
            self._contact_info = contact_info
            self._increment_version()

    @property
    def address(self) -> Address | None:
        self._check_not_discarded()
        return self._address
    
    @address.setter
    def address(self, address: Address) -> None:
        self._check_not_discarded()
        if (self._address != address):
            self._address = address
            self._increment_version()

    @property
    def menus(self) -> list[Menu]:
        self._check_not_discarded()
        return [menu for menu in self._menus if not menu.discarded]
    
    def create_menu(self, *, description: str, tags: list[Tag]) -> None:
        self._check_not_discarded()
        menu = Menu.create_menu(
            author_id=self._author_id,
            client_id=self.id,
            description=description,
            tags=tags,
        )
        self._menus.append(menu)
        self._increment_version()

    def delete_menu(self, menu: Menu) -> None:
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
        if (self._notes != notes):
            self._notes = notes
            self._increment_version()

    @property
    def tags(self) -> list[Tag]:
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: list[Tag]) -> None:
        self._check_not_discarded()
        for tag in value:
            Client.check_rule(
                AuthorIdOnTagMustMachRootAggregateAuthor(tag, self),
            )
        self._tags = value
        self._increment_version()

    @property
    def created_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._created_at
    
    @property
    def updated_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._updated_at
    
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
