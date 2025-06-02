from __future__ import annotations

from functools import lru_cache
import uuid
from datetime import datetime


from src.contexts.recipes_catalog.core.domain.events.menu.menu_deleted import (
    MenuDeleted,
)
from src.contexts.recipes_catalog.core.domain.events.menu.menu_meals_changed import (
    MenuMealAddedOrRemoved,
)
from src.contexts.recipes_catalog.core.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
)
from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import MenuMeal
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event

from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.logging.logger import logger

class Menu(Entity):
    def __init__(
        self,
        *,
        id: str,
        author_id: str,
        client_id: str,
        meals: set[MenuMeal] | None = None,
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
        self._meals = meals or set()
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
        client_id: str,
        menu_id: str,
        tags: set[Tag] | None = None,
        description: str | None = None,
    ) -> "Menu":
        menu = cls(
            id=menu_id,
            author_id=author_id,
            client_id=client_id,
            tags=tags,
            description=description,
        )
        return menu


    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def client_id(self) -> str :
        self._check_not_discarded()
        return self._client_id

    @lru_cache
    def get_meals_dict(self) -> dict[tuple[int: 'the week number', str: 'day of the week', str: 'type of meal'], MenuMeal]: # type: ignore
        self._check_not_discarded()
        new_meals = {}
        for meal in self._meals:
            key = (meal.week, meal.weekday, meal.meal_type)
            new_meals[key] = meal
        return new_meals
    
    @lru_cache
    def _ids_of_meals_on_menu(self) -> set[str]:
        self._check_not_discarded()
        return {meal.meal_id for meal in self._meals}
       

    @property
    def meals(self) -> set[MenuMeal]:
        self._check_not_discarded()
        return self._meals

    @meals.setter
    def meals(self, value: set[MenuMeal]) -> None:
        self._check_not_discarded()
        ids_of_meals_on_value = {meal.meal_id for meal in value}
        ids_of_meals_added = ids_of_meals_on_value - self._ids_of_meals_on_menu()
        ids_of_meals_removed = self._ids_of_meals_on_menu() - ids_of_meals_on_value
        self._meals = value
        self.events.append(
            MenuMealAddedOrRemoved(
                menu_id=self.id,
                ids_of_meals_added=ids_of_meals_added,
                ids_of_meals_removed=ids_of_meals_removed,
            )
        )
        self._increment_version()
        type(self).get_meals_dict.cache_clear()
        type(self)._ids_of_meals_on_menu.cache_clear()
        type(self).get_meals_by_ids.cache_clear()

    def add_meal(self, meal: MenuMeal) -> None:
        self._check_not_discarded()
        self._meals.add(meal)
        self.events.append(
            MenuMealAddedOrRemoved(
                menu_id=self.id,
                ids_of_meals_added={meal.meal_id},
                ids_of_meals_removed=set(),
            )
        )
        self._increment_version()
        type(self).get_meals_dict.cache_clear()
        type(self)._ids_of_meals_on_menu.cache_clear()
        type(self).get_meals_by_ids.cache_clear()

    @property
    def sorted_meals(self) -> list[MenuMeal]:
        self._check_not_discarded()
        sorted_weekdays = ['Seg','Ter','Qua','Qui', 'Sex', 'Sab', 'Dom']
        sorted_meals = sorted(
            self._meals,
            key=lambda meal: (
                meal.week,
                sorted_weekdays.index(meal.weekday),
                # meal.meal_type,
            ),
        )
        return sorted_meals
        

    @lru_cache
    def get_meals_by_ids(self, meals_ids: set[str]) -> set[MenuMeal]:
        self._check_not_discarded()
        logger.debug(f"Getting meals by ids: {meals_ids}")
        return {meal for meal in self._meals if meal.meal_id in meals_ids}


    def update_meal(self, meal: MenuMeal) -> None:
        self._check_not_discarded()
        try: 
            logger.debug(f"Updating meal {meal} on menu {self.id}")
            self._meals.remove(meal)
            self._meals.add(meal)
            type(self).get_meals_dict.cache_clear()
        except KeyError:
            logger.warning(f"Tried to remove meal that is not on menu. Menu: {self.id}. Meal: {meal.meal_id}")
            return
        self._increment_version()

    def filter_meals(
        self,
        *,
        week: int | None = None,
        weekday: str | None = None,
        meal_type: str | None = None,
    ) -> list[MenuMeal]:
        self._check_not_discarded()
        if None not in (week, weekday, meal_type):
            meal = self.get_meals_dict().get((week, weekday, meal_type), None)
            if meal:
                return [meal]
            return []
        meals = []
        for meal in self.get_meals_dict().values():
            if week is not None and meal.week != week:
                continue
            if weekday is not None and meal.weekday != weekday:
                continue
            if meal_type is not None and meal.meal_type != meal_type:
                continue
            meals.append(meal)
        return meals

    def remove_meals(self, meals_ids: frozenset) -> None:
        self._check_not_discarded()
        meals = self.get_meals_by_ids(meals_ids)
        updated_meals = {i for i in (self._meals - meals)}
        self.meals = updated_meals

    @property
    def weekday_of_first_meal(self) -> str:
        self._check_not_discarded()
        sorted_weekdays = ['Seg','Ter','Qua','Qui', 'Sex', 'Sab', 'Dom']
        meals_on_first_week = self.filter_meals(week=1)
        sorted_meals = sorted(
            meals_on_first_week,
            key=lambda meal: sorted_weekdays.index(meal.weekday),
        )
        if not sorted_meals:
            raise ValueError("No meals found on week 1")
        first_meal = sorted_meals[0].weekday
        return first_meal
        

    @property
    def description(self) -> str | None:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def tags(self) -> set[Tag]:
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: set[Tag]) -> None:
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
        self.events.append(
            MenuDeleted(
                menu_id=self.id,
            )
        )
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
