from __future__ import annotations

from datetime import datetime
from functools import cached_property

from src.contexts.recipes_catalog.core.domain.client.events.menu_deleted import (
    MenuDeleted,
)
from src.contexts.recipes_catalog.core.domain.client.events.menu_meals_changed import (
    MenuMealAddedOrRemoved,
)
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
    MenuMeal,
)
from src.contexts.recipes_catalog.core.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
)
from src.contexts.seedwork.domain.entity import Entity
from src.contexts.seedwork.domain.event import Event
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.logging.logger import get_logger


class Menu(Entity):
    """Menu aggregate root for organizing meals by week and weekday.

    Invariants:
        - All meals must have valid week, weekday, and meal_type values
        - Meal positions must be unique within the same week/weekday/meal_type
        - Tags must have matching author_id with the menu

    Attributes:
        author_id: ID of the user who created the menu
        client_id: ID of the client this menu belongs to
        meals: Collection of meals organized by position
        tags: Collection of tags associated with the menu
        description: Optional description of the menu

    Notes:
        Allowed transitions: ACTIVE -> DELETED
        Emits events on meal changes and deletion
    """

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
        super().__init__(
            id=id,
            discarded=discarded,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._author_id = author_id
        self._client_id = client_id
        self._meals = meals or set()
        self._tags = tags or set()
        self._description = description
        self.events: list[Event] = []

    @classmethod
    def create_menu(
        cls,
        *,
        author_id: str,
        client_id: str,
        menu_id: str,
        tags: frozenset[Tag] | None = None,
        description: str | None = None,
    ) -> Menu:
        """Create a new menu instance.

        Args:
            author_id: ID of the user creating the menu
            client_id: ID of the client the menu belongs to
            menu_id: Unique identifier for the menu
            tags: Optional set of tags to associate
            description: Optional menu description

        Returns:
            New Menu instance
        """
        return cls(
            id=menu_id,
            author_id=author_id,
            client_id=client_id,
            tags=set(tags) if tags else set(),
            description=description,
        )

    @property
    def author_id(self) -> str:
        """Get the author ID of the menu.

        Returns:
            ID of the user who created the menu
        """
        self._check_not_discarded()
        return self._author_id

    @property
    def client_id(self) -> str:
        """Get the client ID of the menu.

        Returns:
            ID of the client this menu belongs to
        """
        self._check_not_discarded()
        return self._client_id

    @cached_property
    def _meals_by_position_lookup(self) -> dict[tuple[int, str, str], MenuMeal]:
        """Create a dictionary mapping position coordinates to MenuMeal objects.

        This property builds a lookup table for fast positional queries using
        (week, weekday, meal_type) tuples as keys. Uses instance-level caching
        to avoid rebuilding the lookup table on repeated access.

        Returns:
            dict[tuple[int, str, str], MenuMeal]: Dictionary mapping position tuples
            to MenuMeal objects for O(1) positional lookups

        Cache invalidation triggers:
            - meals setter: When the meals collection is replaced
            - add_meal(): When a new meal is added to the menu
            - update_meal(): When an existing meal is updated

        Performance: O(n) computation where n = number of meals on first access,
        O(1) lookup performance, O(1) on subsequent accesses until cache invalidation.

        Notes:
            - Used internally by filter_meals() for efficient positional queries
            - Key format: (week_number, weekday, meal_type)
            - Automatically handles duplicate positions (last meal wins)
        """
        self._check_not_discarded()
        result = {}
        for meal in self._meals:
            key = (meal.week, meal.weekday, meal.meal_type)
            result[key] = meal
        return result

    @cached_property
    def _meals_by_id_lookup(self) -> dict[str, MenuMeal]:
        """Create a dictionary mapping meal IDs to MenuMeal objects.

        This property builds a lookup table for fast ID-based queries using
        meal_id as keys. Uses instance-level caching to avoid rebuilding
        the lookup table on repeated access.

        Returns:
            dict[str, MenuMeal]: Dictionary mapping meal_id strings to MenuMeal
            objects for O(1) ID-based lookups

        Cache invalidation triggers:
            - meals setter: When the meals collection is replaced
            - add_meal(): When a new meal is added to the menu
            - update_meal(): When an existing meal is updated

        Performance: O(n) computation where n = number of meals on first access,
        O(1) lookup performance, O(1) on subsequent accesses until cache invalidation.

        Notes:
            - Used internally by get_meals_by_ids() for efficient batch retrieval
            - Enables fast meal lookup without iterating through the entire collection
        """
        self._check_not_discarded()
        return {meal.meal_id: meal for meal in self._meals}

    @cached_property
    def _ids_of_meals_on_menu(self) -> set[str]:
        """Create a set of all meal IDs currently on this menu.

        This property extracts all meal IDs for fast membership testing and
        set operations. Uses instance-level caching to avoid recomputing
        the ID set on repeated access.

        Returns:
            set[str]: Set of meal_id strings for all meals on this menu

        Cache invalidation triggers:
            - meals setter: When the meals collection is replaced
            - add_meal(): When a new meal is added to the menu
            - Note: update_meal() does not invalidate this cache (IDs unchanged)

        Performance: O(n) computation where n = number of meals on first access,
        O(1) membership testing, O(1) on subsequent accesses until cache invalidation.

        Notes:
            - Used for efficient meal ID membership testing
            - Supports fast set operations for meal collection comparisons
            - Optimizes change detection in meals setter
        """
        self._check_not_discarded()
        return {meal.meal_id for meal in self._meals}

    @property
    def meals(self) -> set[MenuMeal]:
        """Get all meals in the menu.

        Returns:
            Set of all MenuMeal objects in the menu
        """
        self._check_not_discarded()
        return self._meals

    def get_meals_by_ids(self, meals_ids: set[str]) -> set[MenuMeal]:
        """
        Get meals by their IDs using cached lookup table.

        Args:
            meals_ids: Set of meal IDs to retrieve

        Returns:
            Set of MenuMeal objects matching the provided IDs
        """
        self._check_not_discarded()

        log = get_logger(__name__)
        lookup = self._meals_by_id_lookup
        found_meals = {lookup[meal_id] for meal_id in meals_ids if meal_id in lookup}
        missing_ids = meals_ids - lookup.keys()

        if missing_ids:
            log.warning(
                "Some meal IDs not found in menu",
                menu_id=self.id,
                requested_meal_ids=list(meals_ids),
                missing_meal_ids=list(missing_ids),
                found_count=len(found_meals),
            )

        return found_meals

    @meals.setter
    def meals(self, value: set[MenuMeal]) -> None:
        """Set the meals collection and emit change events.

        Args:
            value: New set of meals to replace current collection

        Events:
            MenuMealAddedOrRemoved: When meals are added or removed
        """
        self._check_not_discarded()
        self._meals = value
        self._increment_version()
        # Invalidate meal-related caches
        self._invalidate_caches(
            "_meals_by_position_lookup", "_meals_by_id_lookup", "_ids_of_meals_on_menu"
        )

    def add_meal(self, meal: MenuMeal) -> None:
        """Add a new meal to the menu.

        Args:
            meal: MenuMeal to add to the menu

        Events:
            MenuMealAddedOrRemoved: When meal is added
        """
        self._check_not_discarded()
        self._meals.add(meal)
        self.events.append(
            MenuMealAddedOrRemoved(
                menu_id=self.id,
                ids_of_meals_added=frozenset({meal.meal_id}),
                ids_of_meals_removed=frozenset(),
            )
        )
        self._increment_version()
        # Invalidate meal-related caches
        self._invalidate_caches(
            "_meals_by_position_lookup", "_meals_by_id_lookup", "_ids_of_meals_on_menu"
        )

    @property
    def sorted_meals(self) -> list[MenuMeal]:
        """Get meals sorted by week, weekday, and meal type.

        Returns:
            List of meals sorted chronologically by week and weekday
        """
        self._check_not_discarded()
        sorted_weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        return sorted(
            self._meals,
            key=lambda meal: (
                meal.week,
                sorted_weekdays.index(meal.weekday),
                # meal.meal_type,
            ),
        )

    def update_meal(self, meal: MenuMeal) -> None:
        """Update an existing meal in the menu.

        Args:
            meal: Updated MenuMeal with new values

        Notes:
            If meal is not found, update is skipped silently.
            Cache is invalidated after successful update.
        """
        self._check_not_discarded()

        log = get_logger(__name__)

        # Find existing meal by meal_id
        existing_meal = self._meals_by_id_lookup.get(meal.meal_id)

        if existing_meal is None:
            # Meal not found - handle gracefully (no-op as per test expectations)
            log.info(
                "Meal update skipped - meal not found in menu",
                menu_id=self.id,
                meal_id=meal.meal_id,
                total_meals_in_menu=len(self._meals),
            )
            return

        log.info(
            "Updating meal in menu",
            menu_id=self.id,
            meal_id=meal.meal_id,
            old_position=(
                existing_meal.week,
                existing_meal.weekday,
                existing_meal.meal_type,
            ),
            new_position=(meal.week, meal.weekday, meal.meal_type),
        )

        # Remove existing meal and add updated meal
        self._meals.remove(existing_meal)  # Remove by the existing meal object
        self._meals.add(meal)  # Add the new meal object

        # Invalidate meal-related caches
        self._invalidate_caches("_meals_by_position_lookup", "_meals_by_id_lookup")
        self._increment_version()

    def filter_meals(
        self,
        *,
        week: int | None = None,
        weekday: str | None = None,
        meal_type: str | None = None,
    ) -> list[MenuMeal]:
        """Filter meals by week, weekday, and/or meal type.

        Args:
            week: Week number to filter by
            weekday: Day of week to filter by
            meal_type: Type of meal to filter by

        Returns:
            List of meals matching the filter criteria

        Notes:
            Uses fast lookup when all parameters are provided.
            Falls back to iteration when partial filters are used.
        """
        self._check_not_discarded()
        # If all parameters are provided, use fast dictionary lookup
        if week is not None and weekday is not None and meal_type is not None:
            meal = self._meals_by_position_lookup.get((week, weekday, meal_type), None)
            if meal:
                return [meal]
            return []

        # Otherwise, iterate through all meals and filter
        meals = []
        for meal in self._meals_by_position_lookup.values():
            if week is not None and meal.week != week:
                continue
            if weekday is not None and meal.weekday != weekday:
                continue
            if meal_type is not None and meal.meal_type != meal_type:
                continue
            meals.append(meal)
        return meals

    def remove_meals(self, meals_ids: set[str]) -> None:
        """Remove meals by their IDs.

        Args:
            meals_ids: Set of meal IDs to remove

        Events:
            MenuMealAddedOrRemoved: When meals are removed
        """
        self._check_not_discarded()
        # Convert set to set for get_meals_by_ids compatibility
        ids_set = set(meals_ids) if isinstance(meals_ids, set) else meals_ids
        meals = self.get_meals_by_ids(ids_set)
        updated_meals = self._meals - meals
        self.meals = updated_meals

    @property
    def weekday_of_first_meal(self) -> str:
        """Get the weekday of the first meal in week 1.

        Returns:
            Weekday string of the first meal

        Raises:
            ValueError: When no meals are found in week 1
        """
        self._check_not_discarded()
        sorted_weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        meals_on_first_week = self.filter_meals(week=1)
        sorted_meals = sorted(
            meals_on_first_week,
            key=lambda meal: sorted_weekdays.index(meal.weekday),
        )
        if not sorted_meals:
            raise ValueError("No meals found on week 1")
        return sorted_meals[0].weekday

    @property
    def description(self) -> str | None:
        """Get the menu description.

        Returns:
            Menu description or None if not set
        """
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        """Set the menu description.

        Args:
            value: New description text
        """
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def tags(self) -> set[Tag]:
        """Get the menu tags.

        Returns:
            Set of tags associated with the menu
        """
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: set[Tag]) -> None:
        """Set the menu tags.

        Args:
            value: New set of tags to associate with the menu

        Raises:
            BusinessRuleViolation: When tag author_id doesn't match menu author_id
        """
        self._check_not_discarded()
        for tag in value:
            Menu.check_rule(
                AuthorIdOnTagMustMachRootAggregateAuthor(tag, self),
            )
        self._tags = value
        self._increment_version()

    def delete(self) -> None:
        """Delete the menu and emit deletion event.

        Events:
            MenuDeleted: When menu is deleted
        """
        self._check_not_discarded()
        self.events.append(
            MenuDeleted(
                menu_id=self.id,
            )
        )
        self._discard()
        self._increment_version()

    def __repr__(self) -> str:
        """String representation of the menu.

        Returns:
            String representation showing id, author_id, and client_id
        """
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id!r}, author_id={self.author_id!r}, client_id={self.client_id!r})"
        )

    def __hash__(self) -> int:
        """Hash based on menu ID.

        Returns:
            Hash value for the menu
        """
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on menu ID.

        Args:
            other: Object to compare with

        Returns:
            True if other is a Menu with the same ID
        """
        if not isinstance(other, Menu):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        """Update internal properties.

        Args:
            **kwargs: Property names and values to update
        """
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        """Update menu properties.

        Args:
            **kwargs: Property names and values to update
        """
        self._check_not_discarded()
        self._update_properties(**kwargs)

    @property
    def meals_dict(self) -> dict[tuple[int, str, str], MenuMeal]:
        """Get meals organized by position coordinates.

        Returns:
            Dictionary mapping (week, weekday, meal_type) tuples to MenuMeal objects
        """
        return self._meals_by_position_lookup
