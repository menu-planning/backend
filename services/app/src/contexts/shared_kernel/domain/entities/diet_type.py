from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime

from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Privacy


class DietType(Entity):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        description: str | None = None,
        privacy: Privacy = Privacy.PRIVATE,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new DietType."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._name = name
        self._author_id = author_id
        self._description = description
        self._privacy = privacy
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def create(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
        privacy: Privacy = Privacy.PRIVATE,
        id: str | None = None,
    ) -> "DietType":
        return cls(
            id=id if id else uuid.uuid4().hex,
            name=name,
            author_id=author_id,
            description=description,
            privacy=privacy,
        )

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

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
    def privacy(self) -> Privacy:
        self._check_not_discarded()
        return self._privacy

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
        if not isinstance(other, DietType):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)

    def model_dump(self) -> Mapping:
        self._check_not_discarded()
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "description": self.description,
            "privacy": self.privacy.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "discarded": self.discarded,
            "version": self.version,
        }
