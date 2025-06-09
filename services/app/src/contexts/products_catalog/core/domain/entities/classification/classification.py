from abc import abstractmethod
from datetime import datetime

from src.contexts.products_catalog.core.domain.events import ClassificationCreated
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.event import Event
from typing import Type, TypeVar

C = TypeVar("C", bound="Classification")

class Classification(Entity):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        description: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Tag."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._name = name
        self._author_id = author_id
        self._description = description
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def _create_classification(
        cls: Type[C],
        *,
        name: str,
        author_id: str,
        event_type: type[ClassificationCreated],
        description: str | None = None,
    ) -> C:
        event = event_type(
            name=name,
            author_id=author_id,
            description=description,
        )
        classification = cls(
            id=event.classification_id,
            name=event.name,
            author_id=event.author_id,
            description=event.description,
        )
        classification.events.append(event)
        return classification

    @classmethod
    @abstractmethod
    def create_classification(
        cls: Type[C],
        *,
        name: str,
        author_id: str,
        event_type: type[ClassificationCreated],
        description: str | None = None,
    ) -> C:
        pass


    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def description(self) -> str | None:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str | None) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
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
            f"(id={self.id!r}, name={self.name!r}, author={self.author_id!r})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Classification):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)
