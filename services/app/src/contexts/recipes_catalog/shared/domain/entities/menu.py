from __future__ import annotations

import uuid
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
    CannotHaveSameMealTypeInSameDay,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Weekday
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class Menu(Entity):
    def __init__(
        self,
        *,
        id: str,
        author_id: str,
        client_id: str | None = None,
        meals: dict[tuple[int, "Week", Weekday, MealType], MenuMeal] | None = None,
        tags: set[Tag] | None = None,
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
        self._meals = meals or {}
        self._tags = tags or set()
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
        tags: set[Tag] | None = None,
        description: str | None = None,
    ) -> "Menu":
        menu_id = uuid.uuid4().hex
        menu = cls(
            id=menu_id,
            author_id=author_id,
            client_id=client_id,
            tags=tags,
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
    def meals(self) -> set[MenuMeal]:
        self._check_not_discarded()
        return self._meals

    @property
    def filter_meals(
        self, *, week: int | None, weekday: Weekday | None, meal_type: MealType | None
    ) -> list[MenuMeal]:
        self._check_not_discarded()
        if not None in (week, weekday, meal_type):
            return [self._meals[(week, weekday, meal_type)]]
        meals = []
        for meal in self._meals.values():
            if week is not None and meal.week != week:
                continue
            if weekday is not None and meal.weekday != weekday:
                continue
            if meal_type is not None and meal.meal_type != meal_type:
                continue
            meals.append(meal)
        return meals

    def add_meals(self, meals: set[MenuMeal]) -> None:
        self._check_not_discarded()
        new_meals = {}
        for meal in meals:
            self.check_rule(CannotHaveSameMealTypeInSameDay(menu=self, menu_meal=meal))
            key = (meal.week, meal.weekday, meal.meal_type)
            new_meals[key] = meal
        self._meals.update(new_meals)
        self._increment_version()

    def remove_meal(self, week: int, weekday: Weekday, meal_type: MealType) -> None:
        self._check_not_discarded()
        key = (week, weekday, meal_type)
        if key in self._meals:
            del self._meals[key]
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
    def tags(self) -> list[Tag]:
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: list[Tag]) -> None:
        self._check_not_discarded()
        for tag in value:
            Menu.check_rule(
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
