from __future__ import annotations

import uuid
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.rules import (
    CannotHaveSameMealTypeInSameDay,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_item import MenuItem
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Weekday
from src.contexts.shared_kernel.domain.value_objects.name_tag.meal_type import MealType


class Menu(Entity):
    def __init__(
        self,
        *,
        id: str,
        author_id: str,
        client_id: str | None = None,
        items: dict[tuple[int, Weekday, MealType], MenuItem] | None = None,
        diet_types_ids: set[str] | None = None,
        description: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Menu."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._author_id = author_id
        self._client_id = client_id
        self._items = items or {}
        self._diet_types_ids = diet_types_ids or set()
        self._description = description
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def create_menu(
        cls,
        *,
        author_id: str,
        client_id: str | None = None,
        diet_types_ids: set[str] | None = None,
        description: str | None = None,
    ) -> "Menu":
        menu_id = uuid.uuid4().hex
        menu = cls(
            id=menu_id,
            author_id=author_id,
            client_id=client_id,
            diet_types_ids=diet_types_ids,
            description=description,
        )
        return menu

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def client_id(self) -> str | None:
        self._check_not_discarded()
        return self._client_id

    @property
    def items(self) -> dict[tuple[int, Weekday, MealType], MenuItem]:
        self._check_not_discarded()
        return self._items

    def add_item(self, item: MenuItem) -> None:
        self._check_not_discarded()
        key = (item.week, item.weekday, item.meal_type)
        self.check_rule(CannotHaveSameMealTypeInSameDay(menu=self, key=key))
        self._items[key] = item
        self._increment_version()

    def remove_item(self, week: int, weekday: Weekday, meal_type: MealType) -> None:
        self._check_not_discarded()
        key = (week, weekday, meal_type)
        if key in self._items:
            del self._items[key]
            self._increment_version()

    @property
    def description(self) -> str:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def diet_types_ids(self) -> set[str]:
        self._check_not_discarded()
        return self._diet_types_ids

    @diet_types_ids.setter
    def diet_types_ids(self, value: set[str]) -> None:
        self._check_not_discarded()
        if self._diet_types_ids != value:
            self._diet_types_ids = value
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
            f"(id={self.id!r}, author_id={self.author_id!r}, client_id={self.client_id!r})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Menu):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)
