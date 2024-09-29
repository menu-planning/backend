from collections.abc import Mapping
from datetime import date, datetime

from attrs import asdict
from src.contexts.menu_planning.shared.domain.events import ClientCreated
from src.contexts.menu_planning.shared.domain.value_objects.contact_info import (
    ContactInfo,
)
from src.contexts.menu_planning.shared.domain.value_objects.dietary_info import (
    DietaryPreferences,
)
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event


class _Client(Entity):
    def __init__(
        self,
        *,
        id: str,
        owner_id: str,
        name: str,
        surname: str,
        birth: date | None = None,
        contact_info: ContactInfo | None = None,
        dietary_preferences: DietaryPreferences | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ):
        """Do not call directly to create a new Client."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._owner_id = owner_id
        self._name = name
        self._surname = surname
        self._contact_info = contact_info
        self._birth = birth
        self._dietary_preferences = dietary_preferences
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def create_client(
        cls,
        *,
        owner_id: str,
        name: str,
        surname: str,
        contact_info: str | None = None,
        birth: date | None = None,
        dietary_preferences: DietaryPreferences | None = None,
    ) -> "_Client":
        event = ClientCreated(
            name=name,
            surname=surname,
        )
        client = cls(
            id=event.client_id,
            owner_id=owner_id,
            name=event.name,
            surname=event.surname,
            contact_info=contact_info,
            birth=birth,
            dietary_preferences=dietary_preferences,
        )
        client.events.append(event)
        return client

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

    @property
    def owner_id(self) -> str:
        self._check_not_discarded()
        return self._owner_id

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    @name.setter
    def name(self, value: str):
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def surname(self) -> str:
        self._check_not_discarded()
        return self._surname

    @surname.setter
    def surname(self, value: str):
        self._check_not_discarded()
        if self._surname != value:
            self._surname = value
            self._increment_version()

    @property
    def contact_info(self) -> ContactInfo | None:
        self._check_not_discarded()
        return self._contact_info

    @contact_info.setter
    def contact_info(self, value: ContactInfo | None):
        self._check_not_discarded()
        if self._contact_info != value:
            self._contact_info = value
            self._increment_version()

    @property
    def birth(self) -> date | None:
        self._check_not_discarded()
        return self._birth

    @birth.setter
    def birth(self, value: date | None):
        self._check_not_discarded()
        if self._birth != value:
            self._birth = value
            self._increment_version()

    @property
    def dietary_preferences(self) -> DietaryPreferences | None:
        self._check_not_discarded()
        return self._dietary_preferences

    @dietary_preferences.setter
    def dietary_preferences(self, value: DietaryPreferences | None):
        self._check_not_discarded()
        if self._dietary_preferences != value:
            self._dietary_preferences = value
            self._increment_version()

    @property
    def created_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._updated_at

    def delete(self) -> None:
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id!r}, name={self.name!r}, surname={self.surname!r})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Client):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)
